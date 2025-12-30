#!/usr/bin/env python3
"""
Affiliate Program Category Taxonomy

Hierarchical category structure for organizing affiliate programs.
Programs can belong to multiple categories at any level.
"""

# Master taxonomy - each program can be in multiple categories
TAXONOMY = {
    "Sports & Outdoors": {
        "Racket Sports": {
            "Tennis": {},
            "Pickleball": {},
            "Badminton": {},
            "Squash": {},
            "Table Tennis": {},
        },
        "Action Sports": {
            "Skateboarding": {},
            "Surfing": {},
            "Snowboarding": {},
            "BMX": {},
            "Scooters": {},
            "Rollerblading": {},
        },
        "Team Sports": {
            "Football": {},
            "Basketball": {},
            "Soccer": {},
            "Baseball": {},
            "Hockey": {},
            "Volleyball": {},
            "Rugby": {},
            "Lacrosse": {},
        },
        "Golf": {},
        "Cycling": {
            "Road Cycling": {},
            "Mountain Biking": {},
            "E-Bikes": {},
        },
        "Running & Athletics": {},
        "Swimming & Water Sports": {
            "Swimming": {},
            "Kayaking": {},
            "Paddleboarding": {},
            "Fishing": {},
            "Boating": {},
        },
        "Outdoor Recreation": {
            "Camping": {},
            "Hiking": {},
            "Climbing": {},
            "Hunting": {},
        },
        "Fitness & Gym": {
            "Home Gym": {},
            "Workout Equipment": {},
            "Yoga & Pilates": {},
            "CrossFit": {},
        },
        "Combat Sports": {
            "Boxing": {},
            "MMA": {},
            "Wrestling": {},
            "Martial Arts": {},
        },
        "Winter Sports": {
            "Skiing": {},
            "Ice Skating": {},
        },
    },
    "Fashion & Apparel": {
        "Clothing": {
            "Men's Clothing": {},
            "Women's Clothing": {},
            "Kids' Clothing": {},
            "Activewear": {},
            "Streetwear": {},
            "Formal Wear": {},
            "Vintage & Thrift": {},
        },
        "Footwear": {
            "Sneakers": {},
            "Boots": {},
            "Sandals": {},
            "Dress Shoes": {},
            "Athletic Shoes": {},
        },
        "Accessories": {
            "Watches": {},
            "Jewelry": {},
            "Bags & Purses": {},
            "Hats & Caps": {},
            "Sunglasses": {},
            "Belts": {},
        },
        "Print on Demand": {
            "T-Shirts": {},
            "Hoodies": {},
            "Mugs": {},
            "Phone Cases": {},
            "Posters & Prints": {},
            "Stickers": {},
        },
        "Luxury Fashion": {},
        "Sustainable Fashion": {},
    },
    "Technology": {
        "Consumer Electronics": {
            "Smartphones": {},
            "Tablets": {},
            "Laptops": {},
            "Desktops": {},
            "Wearables": {},
            "Audio Equipment": {},
            "Cameras": {},
            "Gaming Consoles": {},
            "TVs & Displays": {},
        },
        "Software": {
            "SaaS": {},
            "Productivity": {},
            "Security": {},
            "Design Tools": {},
            "Developer Tools": {},
            "AI Tools": {},
        },
        "Web Services": {
            "Web Hosting": {},
            "Domain Registration": {},
            "Email Services": {},
            "Cloud Storage": {},
            "VPN": {},
        },
        "Gaming": {
            "PC Gaming": {},
            "Console Gaming": {},
            "Mobile Gaming": {},
            "Game Keys": {},
            "Gaming Gear": {},
        },
        "Smart Home": {
            "Home Automation": {},
            "Security Systems": {},
            "Smart Speakers": {},
        },
    },
    "Home & Garden": {
        "Furniture": {
            "Living Room": {},
            "Bedroom": {},
            "Office Furniture": {},
            "Outdoor Furniture": {},
        },
        "Home Decor": {
            "Wall Art": {
                "Movie Posters": {},
                "Art Prints": {},
                "Canvas Art": {},
                "Photography": {},
            },
            "Rugs & Carpets": {},
            "Lighting": {},
            "Mirrors": {},
            "Clocks": {},
        },
        "Kitchen": {
            "Appliances": {},
            "Cookware": {},
            "Tableware": {},
            "Kitchen Gadgets": {},
        },
        "Bedding & Bath": {},
        "Garden & Patio": {
            "Plants": {},
            "Garden Tools": {},
            "Outdoor Decor": {},
        },
        "Home Improvement": {
            "Tools": {},
            "Paint": {},
            "Flooring": {},
            "Hardware": {},
        },
        "Storage & Organization": {},
    },
    "Health & Wellness": {
        "Supplements": {
            "Vitamins": {},
            "Protein & Fitness": {},
            "Weight Loss": {},
            "Herbal": {},
            "CBD": {},
        },
        "Fitness Equipment": {},
        "Personal Care": {
            "Skincare": {},
            "Haircare": {},
            "Oral Care": {},
            "Body Care": {},
        },
        "Medical & Health Devices": {},
        "Mental Health": {
            "Meditation Apps": {},
            "Therapy Services": {},
        },
        "Vision Care": {
            "Eyeglasses": {},
            "Contact Lenses": {},
        },
        "Nutrition & Diet": {
            "Meal Delivery": {},
            "Diet Programs": {},
        },
    },
    "Beauty & Cosmetics": {
        "Makeup": {},
        "Skincare": {},
        "Haircare": {
            "Hair Products": {},
            "Hair Tools": {},
        },
        "Fragrances": {},
        "Nail Care": {},
        "Beauty Tools": {},
        "Men's Grooming": {},
        "Organic & Natural Beauty": {},
    },
    "Finance & Business": {
        "Banking": {
            "Online Banks": {},
            "Credit Cards": {},
            "Savings Accounts": {},
        },
        "Investing": {
            "Stock Trading": {},
            "Cryptocurrency": {},
            "Robo-Advisors": {},
            "Real Estate Investing": {},
        },
        "Insurance": {
            "Life Insurance": {},
            "Health Insurance": {},
            "Auto Insurance": {},
            "Home Insurance": {},
            "Pet Insurance": {},
        },
        "Loans": {
            "Personal Loans": {},
            "Mortgages": {},
            "Student Loans": {},
            "Business Loans": {},
        },
        "Business Services": {
            "Accounting Software": {},
            "HR & Payroll": {},
            "Legal Services": {},
            "Business Formation": {},
        },
        "Payments & Fintech": {},
        "Tax Services": {},
    },
    "Education & Learning": {
        "Online Courses": {
            "Programming": {},
            "Business": {},
            "Design": {},
            "Marketing": {},
            "Languages": {},
            "Music": {},
        },
        "Certifications": {},
        "K-12 Education": {},
        "Test Prep": {},
        "Tutoring": {},
        "Educational Tools": {},
        "Books & eBooks": {},
    },
    "Travel & Hospitality": {
        "Flights": {},
        "Hotels": {},
        "Vacation Rentals": {},
        "Car Rentals": {},
        "Cruises": {},
        "Travel Insurance": {},
        "Tours & Activities": {},
        "Travel Gear": {},
        "Luggage": {},
    },
    "Food & Beverage": {
        "Meal Kits": {},
        "Grocery Delivery": {},
        "Specialty Foods": {
            "Organic": {},
            "Gourmet": {},
            "International": {},
            "Snacks": {},
        },
        "Coffee & Tea": {},
        "Wine & Spirits": {},
        "Kitchen Appliances": {},
        "Restaurant Delivery": {},
    },
    "Entertainment & Media": {
        "Streaming Services": {
            "Video Streaming": {},
            "Music Streaming": {},
            "Audiobooks": {},
        },
        "Collectibles": {
            "Movie Memorabilia": {},
            "Sports Cards": {},
            "Toys & Figures": {},
            "Coins & Stamps": {},
        },
        "Movies & TV": {},
        "Music": {
            "Instruments": {},
            "Music Gear": {},
            "Sheet Music": {},
        },
        "Books & Magazines": {},
        "Events & Tickets": {},
    },
    "Pets": {
        "Pet Food": {},
        "Pet Supplies": {},
        "Pet Health": {},
        "Pet Insurance": {},
        "Pet Services": {},
        "Dog Products": {},
        "Cat Products": {},
        "Fish & Aquarium": {},
        "Bird Supplies": {},
        "Small Animals": {},
    },
    "Baby & Kids": {
        "Baby Gear": {},
        "Baby Clothing": {},
        "Toys": {
            "Educational Toys": {},
            "Outdoor Toys": {},
            "Video Games": {},
            "Board Games": {},
        },
        "Kids' Furniture": {},
        "Parenting Resources": {},
        "Kids' Activities": {},
    },
    "Automotive": {
        "Auto Parts": {},
        "Car Accessories": {},
        "Car Care": {},
        "Tires": {},
        "Car Electronics": {},
        "Auto Insurance": {},
        "Car Rental": {},
        "Electric Vehicles": {},
        "Motorcycles": {},
    },
    "Arts & Crafts": {
        "Art Supplies": {},
        "Craft Supplies": {},
        "Sewing & Fabric": {},
        "Jewelry Making": {},
        "Scrapbooking": {},
        "Knitting & Crochet": {},
        "Painting": {},
        "Photography": {},
    },
    "Dating & Relationships": {
        "Dating Apps": {},
        "Matchmaking Services": {},
        "Relationship Coaching": {},
        "Wedding Services": {},
    },
    "Green & Sustainable": {
        "Eco-Friendly Products": {},
        "Solar & Renewable Energy": {},
        "Electric Vehicles": {},
        "Sustainable Fashion": {},
        "Zero Waste": {},
    },
    "B2B & Enterprise": {
        "Marketing Tools": {
            "Email Marketing": {},
            "SEO Tools": {},
            "Social Media Tools": {},
            "Analytics": {},
        },
        "CRM": {},
        "Project Management": {},
        "Communication Tools": {},
        "E-commerce Platforms": {},
        "Website Builders": {},
    },
}


def flatten_taxonomy(taxonomy: dict, parent_path: list = None) -> list:
    """Flatten taxonomy into list of (path, name) tuples."""
    if parent_path is None:
        parent_path = []

    result = []
    for name, children in taxonomy.items():
        current_path = parent_path + [name]
        result.append((current_path, name))
        if children:
            result.extend(flatten_taxonomy(children, current_path))

    return result


def get_all_categories() -> list:
    """Get all category paths as strings."""
    flat = flatten_taxonomy(TAXONOMY)
    return [" > ".join(path) for path, name in flat]


if __name__ == "__main__":
    categories = get_all_categories()
    print(f"Total categories: {len(categories)}")
    print("\nSample categories:")
    for cat in categories[:30]:
        print(f"  {cat}")
