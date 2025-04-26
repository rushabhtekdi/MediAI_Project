from flask import Flask, request, jsonify, render_template, redirect, url_for
from helpers import generate_ai_response, generate_mock_response, analyze_medical_report
from config import USE_MOCK_RESPONSE, ANTHROPIC_API_KEY
import os
import math
import requests
from werkzeug.utils import secure_filename

# Add these imports to your app.py
from product_analyzer import analyze_product_health

# For file handling
import tempfile
import os
from PIL import Image
import pytesseract
import io

# For PDF handling
from pdfminer.high_level import extract_text as pdf_extract_text

# For DOCX handling
import docx

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Use environment variable or fallback to the hardcoded value as a last resort
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY","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")
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "pk.0362f2355d5bdc89246e0e1a51dfd9e0")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check-symptoms", methods=["POST"])
def check_symptoms():
    symptoms = request.form.get("symptoms")
    
    # Use the appropriate response generator based on config
    if USE_MOCK_RESPONSE:
        response = generate_mock_response(symptoms)
    else:
        response = generate_ai_response(symptoms)
    
    return jsonify({"result": response})

@app.route('/report-analyzer')
def report_analyzer():
    return render_template('report_analyzer.html')

@app.route('/analyze-report', methods=['POST'])
def analyze_report():
    if 'report' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['report']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not supported. Please upload PDF, DOC, DOCX, JPG, or PNG files."}), 400

    try:
        # Create a secure filename and save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract text based on file type
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        
        extracted_text = ""
        
        # Process based on file type
        if file_ext == 'pdf':
            extracted_text = pdf_extract_text(file_path)
        elif file_ext in ['docx']:
            doc = docx.Document(file_path)
            extracted_text = '\n'.join([para.text for para in doc.paragraphs])
        elif file_ext in ['doc']:
            # Basic handling for .doc files - limited support
            return jsonify({"error": "DOC format has limited support. Please convert to PDF or DOCX for better results."}), 400
        elif file_ext in ['jpg', 'jpeg', 'png']:
            # Use OCR to extract text from image
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)
        
        # Clean up the temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
        # Check if text extraction was successful
        if not extracted_text or len(extracted_text.strip()) < 10:
            return jsonify({"error": "Could not extract meaningful text from the document. Please check the file or try a different format."}), 400

        # Use AI to analyze the medical report
        analysis_result = analyze_medical_report(extracted_text)
        
        return jsonify({"result": analysis_result})
        
    except Exception as e:
        return jsonify({"error": f"An error occurred processing the file: {str(e)}"}), 500

@app.route('/bmi-calculator', methods=['GET', 'POST'])
def bmi_calculator():
    # Existing code...
    bmi = None
    category = None
    body_fat = None
    risk = None
    age = None
    gender = None

    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            height = float(request.form['height'])
            age = int(request.form['age'])
            gender = request.form['gender']  # 'male' or 'female'

            if weight <= 0 or height <= 0 or age <= 0:
                raise ValueError("Weight, height, and age must be positive numbers.")

            # BMI Calculation
            bmi = weight / pow(height / 100, 2)  # Height in meters for proper calculation

            # BMI Categories with more detailed descriptions
            if bmi < 16:
                category = "Severe Underweight"
            elif 16 <= bmi < 17:
                category = "Moderate Underweight"
            elif 17 <= bmi < 18.5:
                category = "Mild Underweight"
            elif 18.5 <= bmi < 21.0:
                category = "Lower Normal Weight"
            elif 21.0 <= bmi < 23.5:
                category = "Mid Normal Weight"
            elif 23.5 <= bmi < 25:
                category = "Upper Normal Weight"
            elif 25 <= bmi < 27.5:
                category = "Overweight Class I"
            elif 27.5 <= bmi < 30:
                category = "Overweight Class II"
            elif 30 <= bmi < 35:
                category = "Obesity Class I (Moderate)"
            elif 35 <= bmi < 40:
                category = "Obesity Class II (Severe)"
            else:
                category = "Obesity Class III (Very Severe)"
            
            # Calculate Body Fat Percentage (BFP) - using more accurate formulas
            if gender == 'male':
                # Improved BFP formula for men
                body_fat = (1.20 * bmi) + (0.23 * age) - 16.2
                
                # Ensure realistic ranges
                if body_fat < 2:
                    body_fat = 2  # Minimum essential fat for men
                elif body_fat > 50:
                    body_fat = 50  # Realistic upper limit
            elif gender == 'female':
                # Improved BFP formula for women
                body_fat = (1.20 * bmi) + (0.23 * age) - 5.4
                
                # Ensure realistic ranges
                if body_fat < 10:
                    body_fat = 10  # Minimum essential fat for women
                elif body_fat > 60:
                    body_fat = 60  # Realistic upper limit

            # Detailed Health Risk Assessment Based on BMI, Age, and Gender
            if bmi < 16:
                risk = "Severe health risk due to significant underweight status. Possible malnutrition, weakened immune system, and hormonal disruptions."
            elif 16 <= bmi < 18.5:
                risk = "Increased risk associated with being underweight. May experience nutritional deficiencies, decreased muscle strength, and compromised immune function."
            elif 18.5 <= bmi < 25:
                if age > 65:
                    risk = "Healthy weight range. For older adults, maintaining this BMI is beneficial for mobility and independence."
                else:
                    risk = "Healthy weight range with lowest risk of weight-related health issues. Maintain regular physical activity and balanced nutrition."
            elif 25 <= bmi < 30:
                if age > 65:
                    risk = "Slightly elevated health risk. For older adults, a slightly higher BMI may be protective against frailty."
                else:
                    risk = "Moderately increased risk of heart disease, type 2 diabetes, high blood pressure, and certain cancers. Consider gradual weight reduction through lifestyle changes."
            elif 30 <= bmi < 35:
                risk = "High risk of cardiovascular disease, metabolic syndrome, sleep apnea, and joint problems. Medical evaluation recommended."
            elif 35 <= bmi < 40:
                risk = "Very high risk of serious health conditions including heart disease, stroke, diabetes, and certain cancers. Medical supervision strongly advised."
            else:
                risk = "Extremely high risk of severe health complications. Immediate medical consultation is strongly recommended for a comprehensive health assessment and intervention plan."
                
            # Add body fat context to risk assessment
            if gender == 'male':
                if body_fat < 6:
                    risk += " Body fat percentage is extremely low, which can affect hormone function and overall health."
                elif 6 <= body_fat <= 13:
                    risk += " Body fat percentage is in the athletic range."
                elif 14 <= body_fat <= 17:
                    risk += " Body fat percentage is in the fitness range."
                elif 18 <= body_fat <= 24:
                    risk += " Body fat percentage is in the acceptable range."
                else:
                    risk += " Body fat percentage is elevated, which may increase metabolic health risks."
            elif gender == 'female':
                if body_fat < 16:
                    risk += " Body fat percentage is extremely low, which can affect hormone function and reproductive health."
                elif 16 <= body_fat <= 20:
                    risk += " Body fat percentage is in the athletic range."
                elif 21 <= body_fat <= 24:
                    risk += " Body fat percentage is in the fitness range."
                elif 25 <= body_fat <= 31:
                    risk += " Body fat percentage is in the acceptable range."
                else:
                    risk += " Body fat percentage is elevated, which may increase metabolic health risks."

        except ValueError as e:
            category = f"Error: {str(e)}"

    return render_template('bmi_calculator.html', bmi=bmi, category=category, body_fat=body_fat, risk=risk, age=age, gender=gender)

# Route for the medical facilities finder page
@app.route("/medical-facilities")
def medical_facilities():
    return render_template('hospitals.html')

@app.route("/nearby-facilities")
def nearby_facilities():
    # Existing code...
    # Get parameters from the request
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    facility_type = request.args.get('type', 'hospital')

    if not lat or not lng:
        return jsonify({"error": "Latitude and longitude are required"})

    # For development/testing, use mock data if needed
    if USE_MOCK_RESPONSE:
        return generate_mock_facilities(lat, lng, facility_type)

    try:
        # Map the facility type to LocationIQ's search keywords
        keyword_mapping = {
            'hospital': 'hospital near',
            'doctor': 'doctor clinic near',
            'pharmacy': 'pharmacy near'
        }

        keyword = keyword_mapping.get(facility_type, 'hospital near')

        # Calculate viewbox for area restriction (approximately 10km radius)
        # 0.1 degrees is roughly 11km at the equator
        viewbox = f"{float(lng)-0.1},{float(lat)-0.1},{float(lng)+0.1},{float(lat)+0.1}"

        # LocationIQ API endpoints
        search_url = "https://us1.locationiq.com/v1/search"

        params = {
            'key': LOCATIONIQ_API_KEY,
            'q': keyword,
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'limit': 15,
            'radius': 10000,  # 10km radius
            'dedupe': 1,      # Remove duplicates
            'viewbox': viewbox,
            'bounded': 1      # Force results within the viewbox
        }

        print(f"Searching for {keyword} near {lat}, {lng}")
        response = requests.get(search_url, params=params)

        if response.status_code != 200:
            print(f"LocationIQ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return jsonify({"error": f"Failed to fetch data from LocationIQ (Status: {response.status_code})"})

        data = response.json()
        print(f"Found {len(data)} results from LocationIQ")

        facilities = []

        for place in data:
            # Calculate distance between user and facility
            distance = calculate_distance(
                float(lat), float(lng), 
                float(place['lat']), float(place['lon'])
            )
            
            # Only include facilities within 20km
            if distance <= 20:
                # Extract name from display_name (first part before the comma)
                display_name = place.get('display_name', 'Unknown Location')
                name_parts = display_name.split(',')
                short_name = name_parts[0].strip() if len(name_parts) > 0 else display_name
                
                # Create facility object
                facility = {
                    'name': short_name,
                    'address': ', '.join(name_parts[1:3]) if len(name_parts) > 2 else display_name,
                    'lat': place['lat'],
                    'lng': place['lon'],
                    'distance': round(distance, 2),
                    'phone': 'N/A'  # LocationIQ doesn't typically provide phone numbers
                }
                
                facilities.append(facility)

        print(f"Filtered to {len(facilities)} relevant facilities within 20km")
        
        # If we still don't have facilities, fall back to mock data
        if len(facilities) == 0:
            print("No nearby facilities found, falling back to mock data")
            mock_response = generate_mock_facilities(lat, lng, facility_type)
            return mock_response
            
        return jsonify({"facilities": facilities})

    except Exception as e:
        print(f"Error in nearby_facilities: {str(e)}")
        return jsonify({"error": "An error occurred while fetching nearby facilities"})

def generate_mock_facilities(lat, lng, facility_type):
    """Generate mock facility data for testing"""
    import random
    
    # Create some random facilities around the user location
    facilities = []
    
    # Map facility type to names
    type_names = {
        'hospital': ['General Hospital', 'Community Hospital', 'Medical Center', 'Emergency Care'],
        'doctor': ['Family Clinic', 'Dr. Smith Practice', 'Medical Associates', 'Health Center'],
        'pharmacy': ['City Pharmacy', 'MediStore', 'HealthDrugs', 'PharmaCare']
    }
    
    names = type_names.get(facility_type, ['Medical Facility'])
    
    # Generate 5 random facilities
    for i in range(5):
        # Create slight variations in lat/lng for the mock facilities
        # Using smaller offsets to ensure they're actually nearby (0.001 is roughly 100m)
        facility_lat = float(lat) + (random.random() - 0.5) * 0.005
        facility_lng = float(lng) + (random.random() - 0.5) * 0.005
        
        # Calculate a mock distance (0.5-3 km)
        distance = round(random.uniform(0.5, 3.0), 2)
        
        # Generate random name
        name = f"{random.choice(names)} {i+1}"
        
        # Add mock phone number
        phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        facility = {
            'name': name,
            'address': f"{random.randint(100, 999)} Example St, City",
            'lat': facility_lat,
            'lng': facility_lng,
            'distance': distance,
            'phone': phone if random.random() > 0.3 else "N/A"  # Some facilities might not have phone numbers
        }
        
        facilities.append(facility)
    
    print(f"Generated {len(facilities)} mock facilities")
    return jsonify({"facilities": facilities})

# Helper function to calculate distance between two points
def calculate_distance(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    
    return c * r

  # Add this route to your app.py
@app.route('/product-analyzer')
def product_analyzer():
    return render_template('product_analyzer.html')

@app.route('/analyze-product', methods=['POST'])
def analyze_product():
    product = request.form.get("product")
    product_type = request.form.get("type")
    
    if not product:
        return jsonify({"error": "No product specified"}), 400
    
    # Use the appropriate response generator based on config
    if USE_MOCK_RESPONSE:
        # Use the updated mock function from product_analyzer.py instead
        from product_analyzer import generate_mock_product_analysis
        response = generate_mock_product_analysis(product, product_type)
    else:
        from product_analyzer import analyze_product_health
        response = analyze_product_health(product, product_type)
    
    return jsonify({"result": response})

# Add this function to app.py
def generate_mock_product_analysis(product, product_type):
    """Generate mock analysis for product health"""
    product_lower = product.lower()
    
    # Define some unhealthy product keywords
    unhealthy_food_keywords = [
        'chips', 'soda', 'candy', 'chocolate', 'doritos', 'cheetos', 
        'mountain dew', 'coca-cola', 'pepsi', 'energy drink', 'cake', 
        'cookie', 'fried', 'fast food'
    ]
    
    unhealthy_personal_keywords = [
        'sulfate', 'paraben', 'phthalate', 'formaldehyde', 'artificial fragrance',
        'aluminum', 'propylene glycol', 'sodium lauryl'
    ]
    
    # Define some moderate health product keywords
    moderate_food_keywords = [
        'granola', 'cereal', 'juice', 'white bread', 'pasta sauce', 'dressing',
        'protein bar', 'flavored yogurt', 'instant oatmeal'
    ]
    
    moderate_personal_keywords = [
        'synthetic', 'fragrance', 'preservative', 'color', 'pantene', 
        'head & shoulders', 'alcohol'
    ]
    
    # Define some healthy alternatives based on product type
    healthy_food_alternatives = {
        'chips': ['Air-popped popcorn', 'Kale chips', 'Roasted chickpeas', 'Vegetable chips (homemade)'],
        'soda': ['Sparkling water with fruit', 'Herbal tea', 'Infused water', 'Kombucha (low sugar)'],
        'candy': ['Fresh fruit', 'Dark chocolate (70%+ cacao)', 'Dried fruit (no added sugar)', 'Fruit leather'],
        'chocolate': ['Dark chocolate (70%+ cacao)', 'Cacao nibs', 'Carob chips'],
        'energy drink': ['Green tea', 'Coconut water', 'Coffee (moderate consumption)'],
        'cake': ['Greek yogurt with fruit', 'Chia pudding', 'Fruit sorbet'],
        'cookie': ['Oatmeal cookies with fruit', 'Dark chocolate dipped strawberries', 'Homemade granola bars'],
        'bread': ['Whole grain bread', 'Sourdough bread', 'Sprouted grain bread'],
        'cereal': ['Steel-cut oatmeal', 'Overnight oats', 'Chia pudding', 'Quinoa breakfast bowl'],
        'juice': ['Whole fruits', 'Smoothies with vegetables', 'Infused water', 'Herbal tea'],
        'granola': ['Homemade granola with nuts and seeds (low sugar)', 'Mix of nuts and seeds', 'Overnight oats'],
        'yogurt': ['Plain Greek yogurt with fresh fruit', 'Kefir', 'Coconut yogurt (unsweetened)']
    }
    
    healthy_personal_alternatives = {
        'shampoo': ['Sulfate-free natural shampoos', 'Shampoo bars', 'Apple cider vinegar rinse'],
        'conditioner': ['Natural conditioners', 'Deep conditioning with coconut oil or avocado'],
        'soap': ['Castile soap', 'Natural glycerin soap', 'Handmade soap with natural oils'],
        'lotion': ['Natural oils (coconut, jojoba, almond)', 'Shea butter', 'Aloe vera gel'],
        'deodorant': ['Natural deodorants with essential oils', 'Magnesium or mineral-based deodorants'],
        'toothpaste': ['Fluoride toothpaste without SLS', 'Natural toothpaste with essential oils'],
        'face wash': ['Oil cleansing method', 'Gentle cleansers with natural ingredients', 'Honey as cleanser']
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
            
            # Find matching alternatives
            for keyword, alts in healthy_food_alternatives.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic alternatives
            if not alternatives:
                alternatives = [
                    "Whole, unprocessed foods",
                    "Fresh fruits and vegetables",
                    "Lean proteins",
                    "Whole grains"
                ]
        
        elif any(keyword in product_lower for keyword in moderate_food_keywords):
            health_rating = "Moderate"
            concerns = [
                "May contain added sugars",
                "Possible presence of refined grains",
                "Some processed ingredients",
                "Moderate nutritional value"
            ]
            
            # Find matching alternatives
            for keyword, alts in healthy_food_alternatives.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic alternatives
            if not alternatives:
                alternatives = [
                    "Less processed versions",
                    "Options with fewer added sugars",
                    "Whole food alternatives",
                    "Homemade versions with controlled ingredients"
                ]
        
        else:
            health_rating = "Healthy"
            concerns = [
                "Generally nutritious, but always check labels",
                "Individual dietary needs may vary",
                "Consider organic options when available"
            ]
            alternatives = [
                "Continue choosing whole, unprocessed foods",
                "Focus on variety in your diet",
                "Consider local and seasonal options when available"
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
            
            # Find matching alternatives
            for keyword, alts in healthy_personal_alternatives.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic alternatives
            if not alternatives:
                alternatives = [
                    "Products with natural, plant-based ingredients",
                    "EWG Verified or certified organic products",
                    "DIY alternatives with simple ingredients"
                ]
        
        elif any(keyword in product_lower for keyword in moderate_personal_keywords):
            health_rating = "Moderate"
            concerns = [
                "Contains some synthetic ingredients",
                "Potential irritants for sensitive skin",
                "May include artificial fragrances"
            ]
            
            # Find matching alternatives
            for keyword, alts in healthy_personal_alternatives.items():
                if keyword in product_lower:
                    alternatives = alts
                    break
            
            # If no specific match, provide generic alternatives
            if not alternatives:
                alternatives = [
                    "Products with fewer synthetic ingredients",
                    "Fragrance-free or naturally scented options",
                    "Products designed for sensitive skin"
                ]
        
        else:
            health_rating = "Healthy"
            concerns = [
                "Generally safe ingredients, but individual sensitivities may vary",
                "Consider environmental impact of packaging",
                "Check for certifications like EWG Verified, COSMOS, or USDA Organic"
            ]
            alternatives = [
                "Continue choosing products with natural ingredients",
                "Look for sustainable packaging options",
                "Consider supporting smaller, transparent brands"
            ]
    
    # Format response
    response = f"""Product: {product}

Health Rating: {health_rating}

Potential Concerns:
{chr(10).join('- ' + concern for concern in concerns)}

Healthier Alternatives:
{chr(10).join('- ' + alt for alt in alternatives)}
"""  # Add the closing triple quotes here


if __name__ == "__main__":
    app.run(debug=True)
