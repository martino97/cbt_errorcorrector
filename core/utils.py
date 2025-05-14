import logging

def setup_logger():
    logger = logging.getLogger('coop_validator')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    file_handler = logging.FileHandler('coop_validator.log')
    console_handler = logging.StreamHandler()
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger