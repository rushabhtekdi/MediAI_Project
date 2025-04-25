import os
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

# Initialize the Anthropic client with your API key
client = Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_product_health(product, product_type):
    """Analyze product health using Claude AI, specifically for Indian market"""
    try:
        # Create a specific prompt for the product health analyzer with India focus
        analysis_prompt = f"""
        Please analyze the health aspects of the following {product_type} product available in India:
        
        {product}
        
        Format your response as follows:
        1. A brief description of the product
        2. Health Rating (Healthy, Moderate, or Less Healthy)
        3. Potential health concerns or ingredients to be aware of
        4. Healthier alternatives that are SPECIFICALLY AVAILABLE IN INDIA
        
        IMPORTANT: When suggesting alternatives, ONLY recommend products that are commonly available in the Indian market.
        Focus on Indian brands, products sold in Indian supermarkets/stores, or traditional Indian alternatives.
        """
        
        # Make the API call
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # You can use other Claude models as needed
            max_tokens=600,
            messages=[
                {
                    "role": "user", 
                    "content": analysis_prompt
                }
            ]
        )
        
        # Extract and return the response content
        return response.content[0].text
    except Exception as e:
        # Fall back to mock response if API call fails
        return generate_mock_product_analysis(product, product_type)


def generate_mock_product_analysis(product, product_type):
    """Generate mock analysis for product health with Indian alternatives"""
    product_lower = product.lower()
    
    # Define some unhealthy product keywords
    unhealthy_food_keywords = [
        'chips', 'soda', 'candy', 'chocolate', 'doritos', 'cheetos', 
        'mountain dew', 'coca-cola', 'pepsi', 'energy drink', 'cake', 
        'cookie', 'fried', 'fast food', 'maggi', 'kurkure', 'biscuits'
    ]
    
    unhealthy_personal_keywords = [
        'sulfate', 'paraben', 'phthalate', 'formaldehyde', 'artificial fragrance',
        'aluminum', 'propylene glycol', 'sodium lauryl'
    ]
    
    # Define some moderate health product keywords
    moderate_food_keywords = [
        'granola', 'cereal', 'juice', 'white bread', 'pasta sauce', 'dressing',
        'protein bar', 'flavored yogurt', 'instant oatmeal', 'parle-g', 'marie'
    ]
    
    moderate_personal_keywords = [
        'synthetic', 'fragrance', 'preservative', 'color', 'pantene', 
        'head & shoulders', 'alcohol', 'clinic plus', 'sunsilk'
    ]
    
    # Define India-specific healthy alternatives
    healthy_food_alternatives_india = {
        'chips': ['Thinnai (Fox Nuts/Makhana)', 'Too Yumm Multigrain Chips', 'The Whole Truth Food Veggie Chips', 'Slurrp Farm Millet Puffs'],
        'kurkure': ['Timios Healthy Snack Sticks', 'Yoga Bar Multigrain Chips', 'Farmley Roasted Makhana', 'Gouri\'s Goodies Seed Mix'],
        'maggi': ['Slurrp Farm Millet Noodles', 'Patanjali Atta Noodles', 'Bambino Whole Wheat Vermicelli', 'MTR Instant Poha'],
        'soda': ['Paperboat Coconut Water', 'Raw Pressery Fruit Juices', 'Dabur Glucose-D in water', 'NatureVit Jal Jeera'],
        'candy': ['Nutty Gritties Dry Fruits', 'True Elements Dry Fruit Bars', 'Healthy Karma Energy Bites', 'Naturally Yours Dates'],
        'chocolate': ['Pascati Organic Dark Chocolate', 'Mason & Co. Dark Chocolate', 'Kocoatrait Dark Chocolate', 'Amul Dark Chocolate'],
        'energy drink': ['Auric Ayurvedic Drinks', 'Dabur Chyawanprash Mixed in Milk', 'B-Natural Fruit Juices', 'Organic India Tulsi Tea'],
        'cake': ['Wheafree Millet Cake Mix', 'Conscious Food Ragi Cake Mix', 'Slurrp Farm Millet Pancakes', 'Traditional Indian sweet dishes like Rava Kesari'],
        'cookie': ['Britannia Nutrichoice', 'Unibic Breakfast Cookies', 'Early Foods Organic Cookies', 'True Elements Seeds Cookies'],
        'bread': ['Rudra\'s Organic Sourdough Bread', 'Brown Tree Whole Wheat Bread', 'TheHealthyBake Multigrain Bread', 'English Oven Atta Bread'],
        'cereal': ['Soulfull Ragi Bites', 'True Elements Steel Cut Oats', 'Yoga Bar Wholegrain Breakfast', 'Kellogg\'s Heart to Heart Oats'],
        'juice': ['Raw Pressery Cold Pressed Juice', 'Paper Boat Coconut Water', 'Fresh homemade nimbu pani', 'B Natural Mixed Fruit Juice No Added Sugar'],
        'granola': ['Monsoon Harvest Toasted Millet Muesli', 'True Elements Fruit & Nut Muesli', 'Yoga Bar Muesli', 'Conscious Food Amaranth Muesli'],
        'yogurt': ['Epigamia Greek Yogurt', 'Milky Mist Greek Yogurt', 'Traditional homemade dahi/curd', 'NutriMoo Greek Yogurt']
    }
    
    healthy_personal_alternatives_india = {
        'shampoo': ['Biotique Bio Kelp Shampoo', 'Khadi Natural Amla & Bhringraj Shampoo', 'Forest Essentials Hair Cleanser', 'SoulTree Hair Cleanser'],
        'conditioner': ['Juicy Chemistry Organic Hair Conditioner', 'Rustic Art Organic Conditioner', 'Kama Ayurveda Hair Conditioner', 'Coconut oil hair massage (traditional Indian method)'],
        'soap': ['Medimix Ayurvedic Soap', 'Mysore Sandal Soap', 'Cinthol Original Soap', 'Himalaya Neem & Turmeric Soap'],
        'lotion': ['Forest Essentials Body Lotion', 'Biotique Bio Coconut Milk Body Lotion', 'Himalaya Cocoa Butter Body Lotion', 'Traditional coconut oil or mustard oil massage'],
        'deodorant': ['Cinthol Deo Stick', 'Nivea Deodorants', 'Biotique Bio Deodorants', 'Himalaya Herbals Deo'],
        'toothpaste': ['Dabur Red Toothpaste', 'Himalaya Complete Care', 'Meswak Toothpaste', 'Patanjali Dant Kanti'],
        'face wash': ['Himalaya Neem Face Wash', 'Biotique Bio Honey Face Wash', 'Khadi Natural Face Wash', 'Forest Essentials Face Wash']
    }
    
    # Set default values
    health_rating = "Moderate"
    concerns = []
    alternatives = []
    
    # Determine health rating for food products
    if product_type == 'food':
        if any(keyword in product_lower for keyword in unhealthy_food_keywords):
            health_rating = "Less Healthy"
            concerns = [
                "High in processed ingredients",
                "May contain artificial additives",
                "Potentially high in sodium, sugar, or unhealthy fats",
                "Low in essential nutrients"
            ]
            
            # Find matching alternatives (India-specific)
            for keyword, alts in healthy_food_alternatives_india.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic India-specific alternatives
            if not alternatives:
                alternatives = [
                    "Fresh fruits and vegetables from local markets",
                    "Traditional Indian snacks like chana, makhana, or roasted peanuts",
                    "Homemade curd or buttermilk",
                    "Ragi or jowar based products"
                ]
        
        elif any(keyword in product_lower for keyword in moderate_food_keywords):
            health_rating = "Moderate"
            concerns = [
                "May contain added sugars",
                "Possible presence of refined grains",
                "Some processed ingredients",
                "Moderate nutritional value"
            ]
            
            # Find matching alternatives (India-specific)
            for keyword, alts in healthy_food_alternatives_india.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic India-specific alternatives
            if not alternatives:
                alternatives = [
                    "Unprocessed traditional Indian grains like ragi, jowar, or bajra",
                    "Locally made products with fewer preservatives",
                    "Homemade traditional alternatives",
                    "Products from Indian organic brands like 24 Mantra, Conscious Food, etc."
                ]
        
        else:
            health_rating = "Healthy"
            concerns = [
                "Generally nutritious, but always check labels",
                "Individual dietary needs may vary",
                "Consider organic options when available in Indian markets"
            ]
            alternatives = [
                "Continue choosing whole, unprocessed foods",
                "Look for local and seasonal produce at Indian farmers markets",
                "Traditional Indian superfoods like turmeric, ghee, amla, etc.",
                "Millets and traditional Indian grains"
            ]
    
    # Determine health rating for personal care products
    else:
        if any(keyword in product_lower for keyword in unhealthy_personal_keywords):
            health_rating = "Less Healthy"
            concerns = [
                "Contains potentially harmful chemicals",
                "May cause skin irritation or allergic reactions",
                "Possible hormone-disrupting ingredients",
                "Environmental concerns"
            ]
            
            # Find matching alternatives (India-specific)
            for keyword, alts in healthy_personal_alternatives_india.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic India-specific alternatives
            if not alternatives:
                alternatives = [
                    "Ayurvedic products from brands like Kama Ayurveda or Forest Essentials",
                    "Traditional Indian personal care ingredients like multani mitti, besan, etc.",
                    "Natural brands available in India like Biotique, Khadi Natural, or SoulTree",
                    "Mamaearth or WOW Skin Science products (widely available in India)"
                ]
        
        elif any(keyword in product_lower for keyword in moderate_personal_keywords):
            health_rating = "Moderate"
            concerns = [
                "Contains some synthetic ingredients",
                "Potential irritants for sensitive skin",
                "May include artificial fragrances"
            ]
            
            # Find matching alternatives (India-specific)
            for keyword, alts in healthy_personal_alternatives_india.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic India-specific alternatives
            if not alternatives:
                alternatives = [
                    "Natural Ayurvedic alternatives from Indian brands",
                    "Traditional Indian herbs and ingredients for personal care",
                    "Forest Essentials or Kama Ayurveda products (premium Indian brands)",
                    "Patanjali or Himalaya products (widely available in India)"
                ]
        
        else:
            health_rating = "Healthy"
            concerns = [
                "Generally safe ingredients, but individual sensitivities may vary",
                "Consider environmental impact of packaging",
                "Check for Indian certifications like COSMOS India or Ayush"
            ]
            alternatives = [
                "Continue choosing products with natural ingredients from Indian brands",
                "Look for eco-friendly packaging options available in India",
                "Support small, local Indian brands with transparent ingredient policies"
            ]
    
    # Format response
    response = f"""Product: {product}

Health Rating: {health_rating}

Potential Concerns:
{chr(10).join('- ' + concern for concern in concerns)}

Healthier Alternatives (Available in India):
{chr(10).join('- ' + alt for alt in alternatives)}
"""
    
    return response