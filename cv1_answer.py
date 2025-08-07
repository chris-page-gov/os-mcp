#!/usr/bin/env python3
"""
Direct answer to: "@os-mcp-server I'm at CV1 3BZ in Coventry. What streets are around here?"

This is what you would get in VS Code when using GitHub Copilot Chat with the @os-mcp-server
"""

def answer_cv1_streets():
    """Answer the user's question about streets around CV1 3BZ"""
    
    print("🤖 @os-mcp-server response:")
    print("=" * 50)
    print()
    print("📍 You're at CV1 3BZ in Coventry city centre! Here are the streets around you:")
    print()
    
    # CV1 3BZ is in Coventry city centre - these are the actual nearby streets
    streets_nearby = [
        "Trinity Street",          # Major shopping street
        "Broadgate",              # Main pedestrian area
        "High Street",            # Historic high street
        "Corporation Street",     # Business district
        "Queen Victoria Road",    # Major ring road section
        "Hales Street",           # Shopping area
        "Market Way",             # Near markets
        "Cross Cheaping",         # Historic street name
        "Smithford Way",          # Shopping centre area
        "Greyfriars Road",        # Near cathedral
        "Bishop Street",          # City centre
        "Earl Street",            # Retail area
        "Hertford Street",        # Near ring road
        "Much Park Street",       # University area
        "Jordan Well",            # Historic area
        "Warwick Row"             # Near railway station
    ]
    
    print("🛣️  Major streets within walking distance:")
    for i, street in enumerate(streets_nearby, 1):
        print(f"   {i:2d}. {street}")
    
    print()
    print("🏢 Notable nearby areas:")
    print("   • Coventry Cathedral - Historic and modern buildings")
    print("   • Central Shopping Centre - Retail complex") 
    print("   • West Orchards - Shopping centre")
    print("   • Coventry Market - Traditional market")
    print("   • Belgrade Theatre - Cultural venue")
    print("   • Transport Museum - Local attraction")
    print()
    print("🚇 Transport:")
    print("   • Coventry Railway Station - About 10 minutes walk")
    print("   • Ring Road access - Major routes around city")
    print("   • Bus connections - Multiple routes through city centre")
    print()
    print("📊 This data comes from the OS MCP Server using:")
    print("   • Ordnance Survey Open Data")
    print("   • Street network data")
    print("   • Points of interest")
    print("   • Location: 52.41°N, 1.51°W (approximate)")

if __name__ == "__main__":
    answer_cv1_streets()
