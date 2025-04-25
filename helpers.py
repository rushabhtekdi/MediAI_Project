import os
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, USE_MOCK_RESPONSE

# Initialize the Anthropic client with your API key
client = Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_ai_response(user_input):
    """Generate a response using Anthropic's Claude API"""
    try:
        # Create a specific prompt for the symptom checker
        symptom_prompt = f"""
        Based on the following symptoms, provide a brief assessment:
        
        {user_input}
        
        Format your response with:
        1. A summary of the symptoms
        2. Urgency level (Mild, Moderate, or Severe)
        3. Diet recommendations
        4. Precautions
        """
        
        # Make the API call
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # You can also use other Claude models
            max_tokens=300,
            messages=[
                {
                    "role": "user", 
                    "content": symptom_prompt
                }
            ]
        )
        
        # Extract and return the response content
        return response.content[0].text
    except Exception as e:
        return f"Sorry, I couldn't analyze your symptoms: {str(e)}"

# Mock response function for development/testing
def generate_mock_response(user_input):
    """Generate a dynamic mock response based on the symptoms provided"""
    # Convert to lowercase for easier matching
    symptoms = user_input.lower()
    
    # Define some symptom categories for matching
    respiratory = ['cough', 'breathing', 'short of breath', 'shortness of breath', 'wheeze']
    digestive = ['stomach', 'nausea', 'vomit', 'diarrhea', 'constipation', 'abdomen', 'abdominal']
    head_related = ['headache', 'migraine', 'dizziness', 'vertigo', 'head', 'vision']
    pain = ['pain', 'ache', 'sore', 'hurt', 'aching']
    fever = ['fever', 'temperature', 'chills', 'sweating']
    skin = ['rash', 'itchy', 'itch', 'skin', 'hives', 'red', 'swelling']
    emergency = ['chest pain', 'cannot breathe', 'unconscious', 'passed out', 
                'stroke', 'numbness', 'seizure', 'allergic reaction']
    
    # Evaluate urgency level
    urgency = "Mild"
    
    # Check for emergency symptoms
    if any(term in symptoms for term in emergency):
        urgency = "Severe"
    # Check for fever combined with other symptoms
    elif any(term in symptoms for term in fever) and (
        any(term in symptoms for term in respiratory) or 
        any(term in symptoms for term in digestive)):
        urgency = "Moderate"
    # Check for multiple symptom categories
    elif sum(any(term in symptoms for term in category) for category in 
            [respiratory, digestive, head_related, pain, fever, skin]) >= 3:
        urgency = "Moderate"
    
    # Generate response based on symptom categories
    response_parts = ["Based on your symptoms:\n\n"]
    
    # Extract mentioned symptoms
    mentioned_symptoms = []
    
    if any(term in symptoms for term in respiratory):
        respiratory_symptoms = [term for term in respiratory if term in symptoms]
        mentioned_symptoms.extend(respiratory_symptoms)
        if "cough" in symptoms:
            if "dry" in symptoms:
                mentioned_symptoms.append("dry cough")
            elif "phlegm" in symptoms or "mucus" in symptoms:
                mentioned_symptoms.append("productive cough")
    
    if any(term in symptoms for term in digestive):
        digestive_symptoms = [term for term in digestive if term in symptoms]
        mentioned_symptoms.extend(digestive_symptoms)
    
    if any(term in symptoms for term in head_related):
        head_symptoms = [term for term in head_related if term in symptoms]
        mentioned_symptoms.extend(head_symptoms)
    
    if any(term in symptoms for term in fever):
        mentioned_symptoms.append("fever")
    
    if any(term in symptoms for term in skin):
        skin_symptoms = [term for term in skin if term in symptoms]
        mentioned_symptoms.extend(skin_symptoms)
    
    # If we didn't match any specific symptoms, use their input
    if not mentioned_symptoms:
        response_parts.append(f"Symptoms: {user_input}\n")
    else:
        # Remove duplicates and format nicely
        unique_symptoms = list(set(mentioned_symptoms))
        response_parts.append(f"Symptoms: {', '.join(unique_symptoms)}\n")
    
    # Add urgency level
    response_parts.append(f"Urgency level: {urgency}\n")
    
    # Add recommendations based on urgency
    if urgency == "Severe":
        response_parts.append("Recommendation: Please seek immediate medical attention. Consider visiting an emergency room or calling emergency services.")
    elif urgency == "Moderate":
        response_parts.append("Recommendation: You should consult with a healthcare provider within the next 24-48 hours. These symptoms warrant professional evaluation.")
    else:  # Mild
        response_parts.append("Recommendation: Monitor your symptoms. Rest, stay hydrated, and use over-the-counter medications as appropriate. If symptoms worsen or persist for more than a few days, consult with a healthcare provider.")
    
    # Add disclaimer
    response_parts.append("\nNote: This is an AI-generated assessment and should not replace professional medical advice.")
    
    return "\n".join(response_parts)

def analyze_medical_report(report_text):
    """Analyze medical report and explain medical terminology"""
    try:
        # Create a specific prompt for the medical report analyzer
        analysis_prompt = f"""
        I'm going to provide you with text extracted from a medical report. Please:

        1. Summarize the key findings of the report in simple language
        2. Identify and explain important medical terms in plain language
        3. Highlight any abnormal results and explain what they could mean
        4. Provide general recommendations based on the findings
        5. Format your response to be easily readable with sections and explanations

        Here's the text from the medical report:

        {report_text}
        
        When explaining medical terms, use this format: 
        - Medical term: [Simple explanation]

        For your summary, focus on the most important information a patient would need to understand.
        """
        
        # Make the API call
        response = client.messages.create(
            # model="claude-3-sonnet-20240229",  # Using a more powerful model for in-depth analysis
            model="claude-3-opus-20240229", # or
            max_tokens=1500,
            messages=[
                {
                    "role": "user", 
                    "content": analysis_prompt
                }
            ]
        )
        
        # Process the response to highlight medical terms
        result = response.content[0].text
        
        # Enhance the output by adding HTML formatting
        enhanced_result = enhance_analysis_with_html(result)
        
        return enhanced_result
    except Exception as e:
        return f"Sorry, I couldn't analyze your medical report: {str(e)}"

def enhance_analysis_with_html(analysis_text):
    """Add HTML formatting to make the medical report analysis more readable"""
    # This is a placeholder function that you can implement to add HTML formatting
    # For now, we'll just return the original text
    return analysis_text