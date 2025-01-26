import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import fitz
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, Team

load_dotenv()

genai.configure(api_key=os.getenv('API_KEY'))
config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain"
}

model1 = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain"
    },
    system_instruction="""
    Please generate a set of interview questions based on the provided resume content. 
    Categorize the questions into the following types:
    - Technical: Questions related to programming, problem-solving, tools, frameworks, or technologies.
    Format your response as a numbered list of questions.
    Example:
    1. Question text 
    """
)


def generate_interview_questions_with_categories(resume_text):
        chat_session = model1.start_chat()

        user_input = f"""
        Based on the following resume content, generate interview questions categorized as:
        - Technical: Questions to evaluate technical expertise and problem-solving.

        Format the response as JSON with this structure. Do not type json above the response. Generate only 5 questions for me:
        [
        {{
            "id": 1,
            "text": "Tell me about a challenging project you've worked on and how you handled it.",
            "category": "behavioral"
        }},
        {{
            "id": 2,
            "text": "What are your greatest strengths and how do they align with this role?",
            "category": "behavioral"
        }}
        ]

        Resume Content:
        {resume_text}
        """

        response = chat_session.send_message(user_input)
        response_text = response.text
        response_text = response_text.strip().split('\n')[1:-1]

        cleaned_response = '\n'.join(response_text)
        return json.loads(cleaned_response)


class InterviewQuestionAPIView(APIView):
    def get(self, request):
        try:
            user = request.user
            if not user.is_authenticated:
                return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

            if not hasattr(user, 'resume') or not user.resume:
                return Response({"error": "User does not have a resume uploaded."}, status=status.HTTP_404_NOT_FOUND)

            resume_path = user.resume.path
            try:
                resume_text = ""
                with fitz.open(resume_path) as doc:
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        resume_text += page.get_text()
            except Exception as e:
                return Response({"error": f"Failed to extract text from resume: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            response = generate_interview_questions_with_categories(resume_text)
            if "error" in response:
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

model2 = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain"
    },
    system_instruction="""
    You are an expert technical interviewer specializing in software engineering 
    and data science roles. These answers are being converted from speech to text so keep that in mind while judging the answers. Be lenient and try to give scores that are medium-high rating"""
)

class BulkScoringAPIView(APIView):
    def post(self, request):
        team_id = request.data.get('team_id')
        team = Team.objects.get(id=team_id)
        prompt = f"""
        Analyze these Q&A pairs and return cumulative score (0-100) as JSON:
        {request.data}
        Only return: {{"score": number}}
        """
        response = model2.generate_content(prompt)
        response_text = response.text
        response_text = response_text.strip().split('\n')[1:-1]
        cleaned_response = json.loads('\n'.join(response_text))
        team.interview_score = cleaned_response['score']
        team.interview_status = 'completed'
        team.save()
        return Response({
            "score": team.interview_score,
            "status": team.interview_status
        }, status=status.HTTP_200_OK)
