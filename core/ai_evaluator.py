import os
import json
import re
import google.generativeai as genai
from core.utils import convert_to_ib_grade
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Try models in order of preference
        model_names = ['gemini-3-pro-preview', 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.0-flash', 'gemini-2.0-flash-lite']
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except Exception as e:
                continue
    except Exception as e:
        model = None

def create_ib_prompt(task_description, submission_content, is_image=False):
    #subject detection
    task_lower = task_description.lower()
    subject = "general"
    
    if any(word in task_lower for word in ["math", "calculate", "solve", "equation", "formula", "graph", "algebra", "geometry", "statistics", "calculus"]):
        subject = "mathematics"
    elif any(word in task_lower for word in ["economics", "economic", "market", "demand", "supply", "gdp", "inflation", "trade", "business"]):
        subject = "economics"
    elif any(word in task_lower for word in ["physics", "force", "energy", "motion", "velocity", "acceleration", "wave", "electricity", "magnetism"]):
        subject = "physics"
    elif any(word in task_lower for word in ["chemistry", "chemical", "reaction", "molecule", "element", "compound", "periodic", "acid", "base"]):
        subject = "chemistry"
    elif any(word in task_lower for word in ["biology", "biological", "cell", "organism", "evolution", "genetics", "ecosystem", "photosynthesis"]):
        subject = "biology"
    elif any(word in task_lower for word in ["history", "historical", "war", "revolution", "century", "empire", "civilization", "culture"]):
        subject = "history"
    elif any(word in task_lower for word in ["language", "english", "literature", "essay", "poem", "novel", "analysis", "writing"]):
        subject = "language"
    
    #subject specific prompts
    if subject == "mathematics":
        criteria = """
        IB Mathematics Assessment Criteria:
        - Correct final answer: 30-40% of total score
        - Clear mathematical reasoning and working: 30-40% 
        - Proper use of mathematical notation: 10-15%
        - Communication and organization: 10-15%
        
        For full marks (7/7 or 90-100%), require:
        - Correct answer AND clear step-by-step solution
        - Proper mathematical notation and units
        - Logical flow of reasoning
        
        For partial credit:
        - Correct method but wrong answer: 60-70%
        - Correct answer but no working: 40-50%
        - Some progress towards solution: 20-40%
        """
    
    elif subject == "economics":
        criteria = """
        IB Economics Assessment Criteria:
        - Knowledge and understanding: 25%
        - Application to real-world examples: 25%
        - Analysis and evaluation: 30%
        - Clear communication and structure: 20%
        
        For full marks (7/7 or 90-100%), require:
        - Demonstrates deep understanding of economic concepts
        - Uses relevant real-world examples
        - Shows clear analysis with economic reasoning
        - Well-structured response with conclusion
        
        For partial credit:
        - Basic understanding shown: 40-60%
        - Some analysis but limited examples: 50-70%
        - Good understanding but poor structure: 60-75%
        """
    
    elif subject == "physics":
        criteria = """
        IB Physics Assessment Criteria:
        - Correct physics principles: 30%
        - Mathematical working and calculations: 30%
        - Units, significant figures, uncertainties: 15%
        - Clear diagrams and explanations: 25%
        
        For full marks (7/7 or 90-100%), require:
        - Correct physics concepts AND calculations
        - Proper units and significant figures
        - Clear diagrams where appropriate
        - Step-by-step working shown
        
        For partial credit:
        - Correct physics but calculation errors: 70-80%
        - Right method but missing units: 60-70%
        - Some physics understanding: 30-50%
        """
    
    else:
        criteria = """
        IB General Assessment Criteria:
        - Understanding of key concepts: 40%
        - Application of knowledge: 30%
        - Communication and structure: 20%
        - Critical thinking: 10%
        
        For full marks (7/7 or 90-100%), require:
        - Clear demonstration of understanding
        - Relevant examples or applications
        - Well-organized response
        - Some critical analysis
        """
    
    if is_image:
        prompt_template = f"""
        You are an experienced IB teacher evaluating student work. Analyze this image submission using IB grading standards.
        
        Task: {task_description}
        Subject: {subject.title()}
        Additional text (if any): {submission_content if submission_content else "No additional text"}
        
        {criteria}
        
        Examine the image carefully and evaluate based on IB standards. Look for:
        - Quality of work shown in the image
        - Completeness of solution/response
        - Clarity of presentation
        - Subject-specific requirements
        
        Convert your evaluation to a 0-100 scale where:
        - 90-100: Excellent (IB Grade 7)
        - 80-89: Very Good (IB Grade 6) 
        - 70-79: Good (IB Grade 5)
        - 60-69: Satisfactory (IB Grade 4)
        - 45-59: Mediocre (IB Grade 3)
        - 25-44: Poor (IB Grade 2)
        - 0-24: Very Poor (IB Grade 1)
        
        Respond strictly in JSON format:
        {{"score": number, "feedback": "Detailed IB-style feedback in English explaining strengths, weaknesses, and how to improve"}}
        """
    else:
        prompt_template = f"""
        You are an IB teacher. Evaluate this student work using IB standards (0-100 scale).
        
        Task: {task_description}
        Subject: {subject.title()}
        Student Answer: {submission_content}
        
        {criteria}
        
        Grading scale:
        90-100: Grade 7 (Excellent)
        80-89: Grade 6 (Very Good)
        70-79: Grade 5 (Good)
        60-69: Grade 4 (Satisfactory)
        45-59: Grade 3 (Mediocre)
        25-44: Grade 2 (Poor)
        0-24: Grade 1 (Very Poor)
        
        Respond in JSON format only:
        {{"score": number_0_to_100, "feedback": "detailed_feedback_with_strengths_weaknesses_and_suggestions"}}
        """
    
    return prompt_template

def evaluate_submission_with_ai(task_description, submission_content, uploads_dir="uploads"):
    
    if not model:
        return 0, "AI evaluation unavailable. model not initialized"
    
    # checking if submission contains an image
    image_file_match = None
    if "[IMAGE_FILE:" in submission_content:
        match = re.search(r'\[IMAGE_FILE:(.*?)\]', submission_content)
        if match:
            image_file_match = match.group(1)
            # Remove the image marker from text content
            submission_content = re.sub(r'\[IMAGE_FILE:.*?\]', '', submission_content).strip()

    #create IB prompt for analysis
    prompt = create_ib_prompt(task_description, submission_content, is_image=False)
 
    try:
        #if image file is there, use vision model
        if image_file_match:
            # Construct full path if it's just a filename
            if not os.path.isabs(image_file_match) and not image_file_match.startswith(uploads_dir):
                full_image_path = os.path.join(uploads_dir, image_file_match)
            else:
                full_image_path = image_file_match
                
            if os.path.exists(full_image_path):
                #load image for vision processing
                from PIL import Image as PILImage
                image = PILImage.open(full_image_path)
                
                #create IB prompt for image analysis
                vision_prompt = create_ib_prompt(task_description, submission_content, is_image=True)
                
                response = model.generate_content([vision_prompt, image])
            else:
                return 0, f"Image not found at {full_image_path}"
        else:
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                }
            )    
            
        response_text = None
        
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]

            # Try to extract text from parts
            try:
                if candidate.content and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
            except Exception as e:
                print(f"error {e}")
                
        if not response_text:
            return 0, "No response from AI."
        
        # Try to parse JSON
        try:
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks
            if '```json' in cleaned_text:
                start = cleaned_text.find('```json') + 7
                end = cleaned_text.find('```', start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            elif '```' in cleaned_text:
                # Handle case with just ```
                start = cleaned_text.find('```') + 3
                end = cleaned_text.find('```', start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            
            result = json.loads(cleaned_text)
            score_100 = result.get('score', 0)
            feedback = result.get('feedback', 'Evaluation error')
            
            # Check that score is in valid range (0-100)
            if isinstance(score_100, (int, float)) and 0 <= score_100 <= 100:
                # Convert from 100-point scale to IB 7-point scale
                ib_score = convert_to_ib_grade(score_100)
                # Return original AI feedback with its formatting (markdown, stars, etc.)
                return ib_score, feedback
            else:
                return 0, f"Incorrect score from AI: {score_100}"
                
        except json.JSONDecodeError as e:
            # Try to find score
            score_match = re.search(r'"score":\s*(\d+)', response_text)
            feedback_match = re.search(r'"feedback":\s*"([^"]+)"', response_text, re.DOTALL)
            
            if score_match:
                score_100 = int(score_match.group(1))
                feedback_text = feedback_match.group(1) if feedback_match else response_text
                
                # Clean up escaped characters
                feedback_text = feedback_text.replace('\\n', '\n').replace('\\"', '"')
                
                if 0 <= score_100 <= 100:
                    ib_score = convert_to_ib_grade(score_100)
                    return ib_score, feedback_text
            
            # If all parsing fails, return minimal score
            return 3, "AI evaluation could not be completed properly. Please review manually."
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 0, f"Error during evaluation: {str(e)}"
