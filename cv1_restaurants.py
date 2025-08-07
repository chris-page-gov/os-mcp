#!/usr/bin/env python3
"""
@os-mcp-server: What restaurants are near CV1 3BZ?
This simulates the response you'd get in VS Code GitHub Copilot Chat
"""

def find_restaurants_cv1():
    print("🍽️ @os-mcp-server: Finding restaurants near CV1 3BZ, Coventry...")
    print("=" * 60)
    print()
    
    print("📍 You're in Coventry city centre! Here are restaurants within walking distance:")
    print()
    
    # Main restaurants near CV1 3BZ (Coventry city centre)
    restaurants = [
        {"name": "Cosy Club", "type": "Restaurant & Bar", "location": "Cathedral Lanes", "walk": "2-3 min"},
        {"name": "Turtle Bay", "type": "Caribbean Restaurant", "location": "West Orchards", "walk": "3-5 min"},
        {"name": "Pizza Express", "type": "Italian Restaurant", "location": "Cathedral Lanes", "walk": "2-3 min"},
        {"name": "Nando's", "type": "Portuguese Chicken", "location": "West Orchards", "walk": "3-5 min"},
        {"name": "Wagamama", "type": "Japanese Noodles", "location": "West Orchards", "walk": "3-5 min"},
        {"name": "Las Iguanas", "type": "Latin American", "location": "West Orchards", "walk": "3-5 min"},
        {"name": "Zizzi", "type": "Italian Restaurant", "location": "Cathedral Lanes", "walk": "2-3 min"},
        {"name": "Prezzo", "type": "Italian Restaurant", "location": "Broadgate", "walk": "1-2 min"},
        {"name": "TGI Friday's", "type": "American Restaurant", "location": "SkyDome", "walk": "5-7 min"},
        {"name": "Browns", "type": "British Brasserie", "location": "Eaton Road", "walk": "8-10 min"},
        {"name": "Miller & Carter", "type": "Steakhouse", "location": "Ring Road", "walk": "10-12 min"},
        {"name": "Slug & Lettuce", "type": "Pub & Restaurant", "location": "Broadgate", "walk": "1-2 min"}
    ]
    
    print("🍽️ Full-service restaurants:")
    print("-" * 30)
    for i, rest in enumerate(restaurants, 1):
        print(f"   {i:2d}. **{rest['name']}** ({rest['walk']})")
        print(f"       {rest['type']} • {rest['location']}")
        print()
    
    print("🏬 Main dining areas:")
    print("-" * 20)
    areas = [
        "**Cathedral Lanes** (2-3 min walk) - Premium dining",
        "**West Orchards** (3-5 min walk) - Food court & chains",
        "**Broadgate** (1-2 min walk) - Cafes & pubs",
        "**SkyDome** (5-7 min walk) - Entertainment complex dining",
        "**Eaton Road** (8-10 min walk) - Independent restaurants"
    ]
    
    for area in areas:
        print(f"   • {area}")
    
    print()
    print("☕ Quick food & coffee:")
    print("-" * 25)
    quick_food = [
        "**Costa Coffee** (Cathedral Lanes) - 2 min",
        "**Starbucks** (West Orchards) - 3 min", 
        "**Greggs** (High Street) - 2 min",
        "**McDonald's** (Corporation Street) - 3 min",
        "**Subway** (Multiple locations) - 2-5 min",
        "**Pret A Manger** (Corporation Street) - 3 min"
    ]
    
    for food in quick_food:
        print(f"   • {food}")
    
    print()
    print("🎯 **Recommendations for CV1 3BZ:**")
    print("   🥇 **Closest**: Prezzo (Broadgate) - 1-2 min walk")
    print("   🍕 **Popular**: Pizza Express (Cathedral Lanes) - 2-3 min")
    print("   🌶️ **Spicy**: Nando's or Las Iguanas (West Orchards) - 3-5 min")
    print("   ☕ **Coffee**: Costa (Cathedral Lanes) - 2 min")
    
    print()
    print("📱 **Tips:**")
    print("   • Most restaurants accept walk-ins")
    print("   • Book ahead for weekend evenings")
    print("   • West Orchards has the most variety")
    print("   • Cathedral Lanes for premium dining")

if __name__ == "__main__":
    find_restaurants_cv1()
