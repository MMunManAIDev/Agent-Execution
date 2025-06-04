"""
LLM Handler Module

Verzorgt de interactie met de Language Model (OpenAI API).
Handelt verzoeken af voor het analyseren van webpagina snapshots en bepalen van acties.
"""

import json
import logging
from typing import Dict, Optional, Any
import openai
from ..config import Config
from ..utils.constants import STATUS_CODES  # Direct uit constants importeren

class LLMHandler:
    """
    Handler voor LLM (Language Model) interacties.
    Gebruikt OpenAI's API om webpagina snapshots te analyseren en acties te bepalen.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialiseer de LLM handler.
        
        Args:
            api_key: Optional OpenAI API key. Als None, gebruikt Config.OPENAI_API_KEY
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.conversation_history = []
        self.logger = logging.getLogger(__name__)
        
        # Valideer API key
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured")
            
        openai.api_key = self.api_key

    def get_llm_action(self, snapshot: str, role: str, goal: str) -> Dict[str, Any]:
        """
        Krijg de volgende actie van het LLM op basis van de huidige situatie.
        
        Args:
            snapshot: JSON string met de huidige webpagina status
            role: De rol die het LLM moet aannemen
            goal: Het doel dat bereikt moet worden
            
        Returns:
            Dict met de volgende actie informatie
        """
        try:
            # Valideer input
            if not snapshot or not role or not goal:
                self.logger.error("Invalid input parameters")
                return self._create_error_response("INVALID_INPUT", "Missing required parameters")

            # Bouw de system prompt
            system_prompt = Config.SYSTEM_PROMPT_TEMPLATE.format(
                role=role,
                goal=goal
            )
            
            # Voeg conversation history toe voor context
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Current webpage state: {snapshot}"}
            ]
            
            # Voeg relevante history toe
            for hist in self.conversation_history[-3:]:  # Laatste 3 interacties
                messages.append(hist)
            
            # Roep OpenAI API aan
            self.logger.debug("Calling OpenAI API")
            response = openai.ChatCompletion.create(
                model=Config.OPENAI_MODEL,
                messages=messages,
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            # Parse response
            action = self._parse_llm_response(response)
            
            # Update conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": json.dumps(action)
            })
            
            # Log success
            self.logger.info(f"Successfully determined next action: {action['type']}")
            return action
            
        except openai.error.InvalidRequestError as e:
            self.logger.error(f"Invalid request to OpenAI API: {str(e)}")
            return self._create_error_response("INVALID_INPUT", str(e))
            
        except openai.error.AuthenticationError as e:
            self.logger.error(f"Authentication error with OpenAI API: {str(e)}")
            return self._create_error_response("NOT_AUTHORIZED", "Invalid API key")
            
        except openai.error.APIError as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return self._create_error_response("SERVER_ERROR", "OpenAI API error")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response: {str(e)}")
            return self._create_error_response("INVALID_INPUT", "Invalid JSON in LLM response")
            
        except Exception as e:
            self.logger.exception("Unexpected error in LLM handler")
            return self._create_error_response("ERROR", str(e))

    def _parse_llm_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse en valideer de LLM response.
        
        Args:
            response: Raw response van OpenAI API
            
        Returns:
            Gevalideerde actie dictionary
            
        Raises:
            ValueError: Als response invalide is
        """
        try:
            content = response.choices[0].message.content.strip()
            action = json.loads(content)
            
            # Valideer required fields
            required_fields = {'type', 'target', 'reasoning'}
            if not all(field in action for field in required_fields):
                raise ValueError(f"Missing required fields: {required_fields - set(action.keys())}")
            
            # Valideer action type
            valid_types = {'CLICK', 'SCROLL', 'INPUT', 'WAIT'}
            if action['type'] not in valid_types:
                raise ValueError(f"Invalid action type: {action['type']}")
            
            # Voeg default values toe indien nodig
            action.setdefault('value', None)
            action.setdefault('progress', 0)
            action.setdefault('next_expected_state', None)
            
            return action
            
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def _create_error_response(self, status_code: str, message: str) -> Dict[str, Any]:
        """
        Creëer een gestandaardiseerde error response.
        
        Args:
            status_code: Een van de STATUS_CODES
            message: Error message
            
        Returns:
            Error response dictionary
        """
        return {
            "type": "ERROR",
            "status": STATUS_CODES[status_code],
            "message": message,
            "target": None,
            "reasoning": f"Error occurred: {message}"
        }

    def clear_history(self) -> None:
        """Reset de conversation history."""
        self.conversation_history.clear()
        self.logger.debug("Conversation history cleared")

    def get_conversation_summary(self) -> str:
        """
        Krijg een samenvatting van de conversation history.
        
        Returns:
            String met samenvatting van de conversatie
        """
        if not self.conversation_history:
            return "No conversation history available"
            
        actions = []
        for msg in self.conversation_history:
            if msg["role"] == "assistant":
                try:
                    action = json.loads(msg["content"])
                    actions.append(f"- {action['type']}: {action['reasoning']}")
                except json.JSONDecodeError:
                    continue
                    
        return "\n".join(actions)