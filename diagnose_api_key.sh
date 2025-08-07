#!/bin/bash
# OS DataHub API Key Diagnostic Script
# Run this to diagnose API key issues

echo "🔍 OS DataHub API Key Diagnostic"
echo "================================"
echo

# Check if environment variable is set
if [ -z "$OS_API_KEY" ]; then
    echo "❌ OS_API_KEY environment variable is not set"
    echo "   Run: export OS_API_KEY=\"your-api-key-here\""
    echo
else
    echo "✅ OS_API_KEY environment variable is set"
    echo "   Length: ${#OS_API_KEY} characters"
    echo "   First 20 chars: ${OS_API_KEY:0:20}..."
    echo
fi

# Test basic API connectivity
echo "🌐 Testing OS DataHub API connectivity..."
echo

if [ -n "$OS_API_KEY" ]; then
    echo "1. Testing collections endpoint (should list available collections):"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "https://api.os.uk/features/ngd/ofa/v1/collections?key=$OS_API_KEY")
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    
    if [ "$http_code" = "200" ]; then
        echo "   ✅ Success! Your API key is working"
        echo "   Available collections:"
        echo "$response" | grep -v "HTTP_CODE:" | jq -r '.collections[].id' 2>/dev/null | head -5 | sed 's/^/      - /'
    elif [ "$http_code" = "401" ]; then
        echo "   ❌ 401 Unauthorized - API key is invalid or missing"
        echo "   Check your OS DataHub project and copy the correct 'Project API Key'"
    elif [ "$http_code" = "403" ]; then
        echo "   ⚠️  403 Forbidden - API key is valid but lacks permissions"
        echo "   You may need PSGA access for full features"
    else
        echo "   ❌ HTTP $http_code - Unexpected error"
        echo "   Response: $(echo "$response" | grep -v "HTTP_CODE:")"
    fi
    
    echo
    echo "2. Testing Open Data collection (should work for all users):"
    response2=$(curl -s -w "\nHTTP_CODE:%{http_code}" "https://api.os.uk/features/ngd/ofa/v1/collections/trn-ntwk-street-1?key=$OS_API_KEY")
    http_code2=$(echo "$response2" | grep "HTTP_CODE:" | cut -d: -f2)
    
    if [ "$http_code2" = "200" ]; then
        echo "   ✅ Open Data access confirmed"
    else
        echo "   ❌ HTTP $http_code2 - Even basic access is failing"
    fi
    
    echo
    echo "3. Testing PSGA collection (requires PSGA license):"
    response3=$(curl -s -w "\nHTTP_CODE:%{http_code}" "https://api.os.uk/features/ngd/ofa/v1/collections/bld-fts-buildingline-1?key=$OS_API_KEY")
    http_code3=$(echo "$response3" | grep "HTTP_CODE:" | cut -d: -f2)
    
    if [ "$http_code3" = "200" ]; then
        echo "   ✅ PSGA access confirmed - you have full access!"
    elif [ "$http_code3" = "403" ]; then
        echo "   ⚠️  403 Forbidden - You have Open Data access only"
        echo "   For full features, you need PSGA access (public sector organizations)"
    else
        echo "   ❌ HTTP $http_code3 - Unexpected error"
    fi
    
else
    echo "❌ Cannot test API - OS_API_KEY not set"
fi

echo
echo "📋 Next steps:"
echo "   • If you get 401: Check your API key format and regenerate if needed"
echo "   • If you get 403: You may need PSGA access for that specific collection"
echo "   • If you get 200: Your API key is working correctly!"
echo
echo "🔗 Useful links:"
echo "   • OS DataHub: https://osdatahub.os.uk/"
echo "   • Your Projects: https://osdatahub.os.uk/projects"
echo "   • PSGA Information: https://www.ordnancesurvey.co.uk/business-government/licensing/using-creating-data-with-os-products/os-opendata"
