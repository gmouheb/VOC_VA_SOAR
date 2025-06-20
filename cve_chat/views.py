from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import requests
import json


import os
from dotenv import load_dotenv


from .models import ChatConversation, ChatMessage
from vulnerabilities.models import Vulnerability

load_dotenv()


@login_required
def chat_interface(request, vulnerability_id=None):
    """
    Render the chat interface for generating Ansible playbooks.
    If vulnerability_id is provided, the chat will be specific to that vulnerability.
    """
    vulnerability = None
    if vulnerability_id:
        vulnerability = get_object_or_404(Vulnerability, pk=vulnerability_id, analyst=request.user)

    # Get or create a conversation for this vulnerability
    conversation = None
    if vulnerability:
        # Check if there's an existing conversation for this vulnerability
        conversation = ChatConversation.objects.filter(
            analyst=request.user,
            vulnerability=vulnerability
        ).first()

        if not conversation:
            # Create a new conversation
            conversation = ChatConversation.objects.create(
                analyst=request.user,
                vulnerability=vulnerability,
                title=f"Remediation for {vulnerability.cve or vulnerability.name}"
            )

    context = {
        'vulnerability': vulnerability,
        'conversation_id': conversation.id if conversation else None,
    }

    return render(request, 'cve_chat/chat_interface.html', context)

@login_required
@require_POST
def send_message(request):
    """
    API endpoint to send a message to the AI and get a response.
    """
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        message_content = data.get('message')
        vulnerability_id = data.get('vulnerability_id')

        if not message_content:
            return JsonResponse({'error': 'Message content is required'}, status=400)

        # Get or create conversation
        if conversation_id:
            conversation = get_object_or_404(ChatConversation, id=conversation_id, analyst=request.user)
        else:
            # Create a new conversation
            title = "New Conversation"
            vulnerability = None

            if vulnerability_id:
                vulnerability = get_object_or_404(Vulnerability, id=vulnerability_id, analyst=request.user)
                title = f"Remediation for {vulnerability.cve or vulnerability.name}"

            conversation = ChatConversation.objects.create(
                analyst=request.user,
                vulnerability=vulnerability,
                title=title
            )

        # Save user message
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )

        # Generate AI response
        # This is a placeholder - in a real implementation, you would call an AI service
        # For now, we'll just return a simple response
        response_content = generate_ai_response(message_content, conversation, vulnerability_id)

        # Save assistant message
        assistant_message = ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=response_content
        )

        return JsonResponse({
            'conversation_id': conversation.id,
            'response': response_content
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_ai_response(message, conversation, vulnerability_id=None):
    """
    Generate a response from the AI using Gemini API.
    """
    from django.conf import settings

    # Gemini API endpoint and key
    GEMINI_API_URL = os.getenv("AI_URL")
    GEMINI_API_KEY = os.getenv("API_KEY") # Replace with actual API key from settings if needed

    # Get vulnerability details if available
    vulnerability = None
    if vulnerability_id:
        try:
            vulnerability = Vulnerability.objects.get(id=vulnerability_id)
        except Vulnerability.DoesNotExist:
            pass

    # Prepare conversation history
    contents = []

    # System message to set the context
    system_prompt = "You are an AI assistant specialized in generating Ansible playbooks to remediate CVE vulnerabilities. Provide detailed, accurate playbooks with clear explanations. reply only with ansible playbooks or to explain the cve and how to remediate it, don't reply to any other messages"

    # Add vulnerability details if available
    if vulnerability:
        system_prompt += f"\n\nThe current vulnerability being discussed is: {vulnerability.name}"
        if vulnerability.cve:
            system_prompt += f"\nCVE ID: {vulnerability.cve}"
        if vulnerability.description:
            system_prompt += f"\nDescription: {vulnerability.description}"
        if vulnerability.affected_asset:
            system_prompt += f"\nAffected Asset: {vulnerability.affected_asset}"

    # Add system message as the first user message
    contents.append({
        "role": "user",
        "parts": [{"text": system_prompt}]
    })

    # Add model's acknowledgment of the instructions
    contents.append({
        "role": "model",
        "parts": [{"text": "I understand. I'll help you generate Ansible playbooks to remediate CVE vulnerabilities. I'll provide detailed explanations and focus on the specific vulnerability you're asking about."}]
    })

    # Add conversation history (limited to last 10 messages to avoid token limits)
    recent_messages = conversation.messages.all().order_by('created_at')[:10]

    # Check if we need to ensure alternating roles
    # If the last message in contents is from "user", the next one should be from "model" and vice versa
    expected_role = "user" if contents[-1]["role"] == "model" else "model"

    for chat_message in recent_messages:
        role = "user" if chat_message.role == "user" else "model"

        # Skip this message if it would result in consecutive messages with the same role
        if role == expected_role or len(contents) <= 2:  # Allow first few messages to establish context
            contents.append({
                "role": role,
                "parts": [{"text": chat_message.content}]
            })
            # Update expected role for next message
            expected_role = "user" if role == "model" else "model"

    # Add the current message
    # Check if the last message in contents is from "user"
    if contents[-1]["role"] == "user":
        # If the last message is from "user", we need to add a model message first
        contents.append({
            "role": "model",
            "parts": [{"text": "I'll help you with that. Please provide more details."}]
        })

    # Now add the current message
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    # Prepare the request payload
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1000,  # Increased to allow for longer responses
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    }

    # Make the API request
    try:
        # Construct the URL correctly
        api_url = f"{GEMINI_API_URL}"

        # Add API key as a query parameter
        if "?" in api_url:
            api_url += f"&key={GEMINI_API_KEY}"
            debug_url = f"{GEMINI_API_URL}&key=<API_KEY_HIDDEN>"
        else:
            api_url += f"?key={GEMINI_API_KEY}"
            debug_url = f"{GEMINI_API_URL}?key=<API_KEY_HIDDEN>"

        # Debug: Print the API URL and payload
        print(f"API URL: {debug_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()

            # Debug: Print the successful response
            print(f"Successful response: {json.dumps(response_data, indent=2)}")

            # Extract the generated text
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]

            # Fallback if we couldn't extract the text properly
            return "I'm having trouble generating a response. Please try again with more details about the vulnerability."
        else:
            # Log the error for debugging
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return f"Sorry, I encountered an error when trying to generate a response. Error code: {response.status_code}"

    except Exception as e:
        # Log the exception for debugging
        print(f"Exception when calling Gemini API: {str(e)}")
        return "Sorry, I encountered an error when trying to generate a response. Please try again later."
