"""
Professional logging configuration for Voice Multi-Agent Accelerator
Provides clean, structured logging without icons for debugging conversation flows.
"""

import logging
import sys
from datetime import datetime
from typing import Optional

class ProfessionalFormatter(logging.Formatter):
    """Custom formatter that provides clean, professional log output."""
    
    def __init__(self):
        super().__init__()
        
    def format(self, record):
        """Format log records with professional, structured output."""
        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Map log levels to clean prefixes
        level_prefixes = {
            'DEBUG': 'DEBUG',
            'INFO': 'INFO',
            'WARNING': 'WARN',
            'ERROR': 'ERROR',
            'CRITICAL': 'CRITICAL'
        }
        
        level_prefix = level_prefixes.get(record.levelname, record.levelname)
        
        # Create component identifier from logger name
        component = record.name.split('.')[-1] if '.' in record.name else record.name
        
        # Format the message with consistent spacing
        formatted_message = f"[{timestamp}] {level_prefix:8} | {component:20} | {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted_message += f"\n{record.exc_text}"
            
        return formatted_message

def setup_professional_logging(level: str = "INFO", enable_console: bool = True, log_file: Optional[str] = None):
    """
    Set up professional logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Whether to enable console output
        log_file: Optional file path for log output
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    formatter = ProfessionalFormatter()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

class ConversationFlowLogger:
    """Specialized logger for conversation flow debugging."""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
    
    def conversation_start(self, session_id: str, connection_type: str):
        """Log conversation session start."""
        self.logger.info(f"Conversation started - Session: {session_id}, Type: {connection_type}")
    
    def user_message(self, session_id: str, message: str, message_type: str = "voice"):
        """Log user message received."""
        truncated = message[:100] + "..." if len(message) > 100 else message
        self.logger.info(f"User message received - Session: {session_id}, Type: {message_type}, Content: '{truncated}'")
    
    def agent_processing(self, session_id: str, agent_name: str, status: str = "processing"):
        """Log agent processing status."""
        self.logger.info(f"Agent processing - Session: {session_id}, Agent: {agent_name}, Status: {status}")
    
    def agent_response(self, session_id: str, agent_name: str, response_length: int, has_card: bool = False):
        """Log agent response generated."""
        card_info = "with card" if has_card else "no card"
        self.logger.info(f"Agent response - Session: {session_id}, Agent: {agent_name}, Length: {response_length} chars, Card: {card_info}")
    
    def voice_api_event(self, session_id: str, event_type: str, details: str = ""):
        """Log Voice Live API events."""
        detail_str = f", Details: {details}" if details else ""
        self.logger.info(f"Voice API event - Session: {session_id}, Type: {event_type}{detail_str}")
    
    def orchestration_flow(self, session_id: str, intent: str, flow_type: str, completion_signals: int = 0):
        """Log orchestration flow decisions."""
        signals_info = f", Completion signals: {completion_signals}" if completion_signals > 0 else ""
        self.logger.info(f"Orchestration flow - Session: {session_id}, Intent: {intent}, Flow: {flow_type}{signals_info}")
    
    def error_occurred(self, session_id: str, component: str, error_type: str, error_msg: str):
        """Log errors with context."""
        self.logger.error(f"Error occurred - Session: {session_id}, Component: {component}, Type: {error_type}, Message: {error_msg}")
    
    def websocket_event(self, session_id: str, event_type: str, details: str = ""):
        """Log WebSocket events."""
        detail_str = f", Details: {details}" if details else ""
        self.logger.info(f"WebSocket event - Session: {session_id}, Type: {event_type}{detail_str}")

# Initialize professional logging on module import
setup_professional_logging()