"""
Utility functions for translating technical error messages to user-friendly formats.
This module provides translation dictionaries and helper functions to convert regex validation errors
and other technical messages into business-friendly language.
"""

# Dictionary mapping error codes to user-friendly messages
ERROR_CODE_TRANSLATIONS = {
    # General error codes
    "UNKNOWN": "An unknown error has occurred with this record.",
    
    # Error code prefixes
    "E": "Critical Error",
    "W": "Warning",
    "C": "Critical Error",
    
    # Specific error codes - add more as needed based on your error patterns
    "E001": "Customer code is missing or invalid",
    "E002": "Required personal information is missing",
    "E003": "Invalid identification document",
    "E004": "Invalid contact information",
    "E005": "Invalid address information",
    "W001": "Missing optional field that is recommended",
    "W002": "Date format is incorrect",
    "C001": "Critical validation error in primary data field",
    
    # Add specific CVC error codes from your screenshot
    "cvc-datatype-valid": "The data format is invalid",
    "cvc-enumeration-valid": "The selected region is not valid",
    "cvc-pattern-valid": "The identification format is invalid"
}

# Dictionary mapping regex validation patterns to user-friendly explanations
REGEX_TRANSLATIONS = {
    # National ID
    r'[0-9]{8}(-[0-9]{5}){2}-[0-9]{2}': "National ID must be in format: YYYYMMDD-XXXXX-XXXXX-XC, where YYYYMMDD is birth date, XXXXX are postal and serial codes, and XC is gender code and checksum",
    
    # Tax identification number
    r'[0-9]{3}(-[0-9]{3}){2}': "Tax ID number must be in format: XXX-XXX-XXX",
    
    # Phone numbers
    r'((\+255[0-9]{9})|(0[0-9]{9})){1}': "Phone number must be in international format (+255XXXXXXXXX) or local format (0XXXXXXXXX)",
    r'((\+255[0-9]{9})|([0-9]{7,9})){1}': "Phone number must be in international format (+255XXXXXXXXX) or local format with 7-9 digits",
    
    # Email
    r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6}': "Email address must be in a valid format (example@domain.com)",
    
    # Passport
    r'[a-zA-Z]{2}[0-9]{6}': "Passport number must be 2 letters followed by 6 digits",
    
    # Driving license
    r'[0-9]{10}': "Driving license (Mainland) must be 10 digits",
    r'[Z]{1}[0-9]{9}': "Driving license (Zanzibar) must start with Z followed by 9 digits",
    
    # Voter registration
    r'[0-9]{8}': "Voter registration number (Mainland) must be 8 digits",
    r'[0-9]{9}': "Voter registration number (Zanzibar) or Zanzibar ID must be 9 digits",
    
    # BOT license number
    r'[M]{1}[S]{1}[P]{1}[0-9]{5}': "BOT license number must start with MSP followed by 5 digits",
    
    # BRELA registration
    r'[0-9]{1,6}': "Registration number must be 1-6 digits",
    r'[Z]{1}[0-9]{10}': "Zanzibar registration number must start with Z followed by 10 digits",
    
    # Postal code
    r'[0-9]{5}': "Postal code must be 5 digits",
    
    # Citizen ID pattern from screenshot
    r'[0-9]{1}[1-9][0-9]{10}': "Citizen ID must be in the correct format"
}

# Dictionary mapping field names to user-friendly descriptions
FIELD_TRANSLATIONS = {
    "CustomerCode": "Customer Code",
    "FirstName": "First Name",
    "MiddleNames": "Middle Names",
    "LastName": "Last Name",
    "BirthSurname": "Birth Surname",
    "Gender": "Gender",
    "MaritalStatus": "Marital Status",
    "Nationality": "Nationality",
    "NumberOfNationalId": "National ID Number",
    "NumberOfPassport": "Passport Number", 
    "NumberOfDrivingLicense": "Driving License Number",
    "NumberOfVoterRegistration": "Voter Registration Number",
    "NumberOfZanzibarId": "Zanzibar ID Number",
    "TaxIdentificationNumber": "Tax ID Number",
    "RegistrationNumber": "Registration Number",
    "BOTlicenceNumber": "BOT License Number",
    "CellularPhone": "Mobile Phone Number",
    "FixedLine": "Landline Number",
    "Email": "Email Address",
    "TradeName": "Business Name",
    "BirthDate": "Date of Birth",
    "EstablishmentDate": "Company Establishment Date",
    "DateOfIssuance": "Document Issue Date",
    "DateOfExpiration": "Document Expiry Date",
    "dateTime": "Date and Time",
    "CITIZEN ID": "Citizen ID"
}

# Business rule translations
BUSINESS_RULE_TRANSLATIONS = {
    "Mandatory": "This field is required and cannot be empty",
    "Individual must be between 18 and 99 years old": "The person must be between 18 and 99 years old",
    "Amount can not be negative": "The amount value cannot be negative",
    "Issuance date must not be greater than reporting date": "The document issue date cannot be in the future",
    "Expiration date must not be less than issuance date": "The expiry date must be after the issue date",
    "Expiration date must not be less than reporting date": "The document cannot be already expired",
    "At least one identification document must be filled in": "At least one ID document (National ID, Passport, etc.) must be provided",
    "Establishment date must be less than reporting date": "The establishment date cannot be in the future",
    "At least one type of contact information is mandatory": "At least one contact method (phone, email, etc.) must be provided",
    "The first eight numerical numbers represent the year, month and day the person was born": "The first 8 digits of the National ID should match the person's date of birth (YYYYMMDD)",
    "Mandatory for all females": "This field is required for female customers"
}

# New specific translation patterns for the error messages in your screenshot
SPECIFIC_ERROR_TRANSLATIONS = {
    "cvc-datatype-valid.1.2.1": "The date format is invalid",
    "is not a valid value for 'dateTime'": "Please enter a valid date and time format",
    "Value 'Region.ARUSHA' is not facet-valid": "The selected region is not in the list of valid regions",
    "Value 'CITIZEN ID' is not facet-valid": "The Citizen ID format is incorrect",
    "[0-9]{1}[1-9][0-9]{10}": "Citizen ID must be a number starting with a digit followed by a non-zero digit and 10 more digits"
}

def get_human_readable_error(error_code=None, field_name=None, regex_pattern=None, business_rule=None, original_message=None):
    """
    Convert technical error information to human-readable format.
    
    Args:
        error_code: The error code from the system
        field_name: The name of the field with the error
        regex_pattern: The regex pattern that failed validation
        business_rule: The business rule that was violated
        original_message: The original error message for specific pattern matching
        
    Returns:
        A human-readable error message
    """
    messages = []
    
    # First check for specific error patterns in the original message
    if original_message:
        for pattern, translation in SPECIFIC_ERROR_TRANSLATIONS.items():
            if pattern in original_message:
                messages.append(translation)
                break
    
    # Start with field name if provided
    if field_name:
        friendly_field = FIELD_TRANSLATIONS.get(field_name, field_name)
        messages.append(f"Issue with: {friendly_field}")
    
    # Add error code translation if available
    if error_code:
        # First try exact match
        if error_code in ERROR_CODE_TRANSLATIONS:
            messages.append(ERROR_CODE_TRANSLATIONS[error_code])
        # Then try prefix match
        elif error_code.split('-')[0] in ERROR_CODE_TRANSLATIONS:
            messages.append(ERROR_CODE_TRANSLATIONS[error_code.split('-')[0]])
    
    # Add regex explanation if available
    if regex_pattern and regex_pattern in REGEX_TRANSLATIONS:
        messages.append(REGEX_TRANSLATIONS[regex_pattern])
    
    # Add business rule explanation if available
    if business_rule:
        # Try exact match
        if business_rule in BUSINESS_RULE_TRANSLATIONS:
            messages.append(BUSINESS_RULE_TRANSLATIONS[business_rule])
        # Try partial match - find the longest matching substring
        else:
            matches = []
            for rule_key in BUSINESS_RULE_TRANSLATIONS:
                if rule_key in business_rule:
                    matches.append((len(rule_key), BUSINESS_RULE_TRANSLATIONS[rule_key]))
            
            if matches:
                # Get the longest match
                matches.sort(reverse=True)
                messages.append(matches[0][1])
    
    # If we couldn't generate any helpful messages, return a default
    if not messages:
        # If we have the original message, use it as a fallback but clean it up
        if original_message:
            # Remove common technical prefixes and clean up the message
            cleaned_message = original_message
            prefixes_to_remove = [
                "cvc-datatype-valid.1.2.1: ",
                "cvc-enumeration-valid: ",
                "cvc-pattern-valid: "
            ]
            for prefix in prefixes_to_remove:
                cleaned_message = cleaned_message.replace(prefix, "")
            
            return f"Validation error: {cleaned_message}"
        return "Validation error occurred. Please check the data and try again."
    
    return " - ".join(messages)

def extract_error_code_from_message(message):
    """
    Extract error code from error message.
    
    Args:
        message: The error message
        
    Returns:
        The extracted error code or None
    """
    import re
    # Look for common error code patterns like cvc-datatype-valid, cvc-enumeration-valid, etc.
    patterns = [
        r"(cvc-\w+(-\w+)*)",
        r"(E\d{3})",
        r"(W\d{3})",
        r"(C\d{3})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)
    
    return None

def extract_field_from_message(message):
    """
    Extract field name from error message.
    
    Args:
        message: The error message
        
    Returns:
        The extracted field name or None
    """
    import re
    field_patterns = [
        r"'(.*?)'",  # Look for content in single quotes
        r"for '(\w+)'",  # Look for field names after "for"
        r"for type '(.*?)'",  # Look for type information
        r"type '(\w+\.\w+\.\w+\.\w+)'" # Look for schema types
    ]
    
    for pattern in field_patterns:
        match = re.search(pattern, message)
        if match:
            field_name = match.group(1)
            # Check if it's in our field translations or extract the last part of the path
            if field_name in FIELD_TRANSLATIONS:
                return field_name
            elif '.' in field_name:
                return field_name.split('.')[-1]
            return field_name
    
    return None

def parse_error_details(message, customer_details):
    """
    Parses the error message and customer details to extract useful information
    for generating a human-readable error message.
    
    Args:
        message: Original error message
        customer_details: Dictionary of additional error details
        
    Returns:
        A human-readable error message
    """
    if not message:
        return "Validation error occurred. Please check the data and try again."
        
    # Extract error code
    error_code = extract_error_code_from_message(message)
    
    # Extract field name
    field_name = extract_field_from_message(message)
    
    # Look for regex patterns in the message
    regex_pattern = None
    for regex in REGEX_TRANSLATIONS:
        if regex in message:
            regex_pattern = regex
            break
    
    # Look for business rules in the message
    business_rule = None
    for rule in BUSINESS_RULE_TRANSLATIONS:
        if rule in message:
            business_rule = rule
            break
    
    # Check customer details for additional info
    if customer_details:
        if not field_name and 'Field' in customer_details:
            field_name = customer_details['Field']
        if not business_rule and 'Rule' in customer_details:
            business_rule = customer_details['Rule']
    
    # Generate the human-readable message
    return get_human_readable_error(
        error_code=error_code,
        field_name=field_name,
        regex_pattern=regex_pattern,  
        business_rule=business_rule,
        original_message=message
    )

def translate_error_message(error):
    """
    Main function to translate an error object into human-readable format.
    
    Args:
        error: CustomerError object
        
    Returns:
        A human-readable error message
    """
    # Extract key information from the error object
    error_code = getattr(error, 'error_code', None)
    message = getattr(error, 'message', '')
    customer_details = getattr(error, 'customer_details', None)
    
    # Start with error code translation if available
    if error_code:
        friendly_message = get_human_readable_error(error_code=error_code, original_message=message)
    else:
        friendly_message = None
    
    # If we have more details in the original message or customer_details, enhance the message
    detailed_message = parse_error_details(message, customer_details)
    
    if friendly_message and detailed_message and friendly_message != detailed_message:
        return f"{friendly_message}: {detailed_message}"
    elif detailed_message:
        return detailed_message
    elif friendly_message:
        return friendly_message
    else:
        return "Validation error occurred. Please check the data and try again."

def get_friendly_error_message(error):
    """
    Main entry point for getting a friendly error message.
    This function is used by views.py to translate error messages.
    
    Args:
        error: An error object or error message string
        
    Returns:
        A human-readable error message
    """
    # If error is a string, try to parse it directly
    if isinstance(error, str):
        return parse_error_details(error, None)
    
    # If error is an object with expected attributes, use translate_error_message
    if hasattr(error, 'error_code') or hasattr(error, 'message') or hasattr(error, 'customer_details'):
        return translate_error_message(error)
    
    # If it's another type of object, try to extract useful information
    error_message = str(error)
    return parse_error_details(error_message, None)


# Additional function to handle specific error message formats seen in your screenshot
def process_dashboard_error(error_code, error_message):
    """
    Special processing for the error dashboard format messages.
    
    Args:
        error_code: The error code shown in the dashboard (e.g. cvc-datatype-valid)
        error_message: The full error message text
        
    Returns:
        A human-readable error message
    """
    # Handle the specific error patterns from your screenshot
    if error_code == "cvc-datatype-valid" and "dateTime" in error_message:
        return "The date format is invalid. Please enter a valid date and time.Expected format is YYYY-MM-DD."
        
    elif error_code == "cvc-enumeration-valid" and "Region.ARUSHA" in error_message:
        return "Invalid region selected. Please select a region from the approved list it should appear as 'eg.Arusha,Dodoma..'."
        
    elif error_code == "cvc-pattern-valid" and "CITIZEN ID" in error_message:
        return "Citizen ID format is incorrect.  It should follow: YYYYMMDD-XXXXX-XXXXX-XX."
    
    elif error_code == "cvc-pattern-valid" and "Tax ID Number" in error_message:
        return "Tax ID Number format is incorrect.  must be in format: XXX-XXX-XXX"
    
    elif error_code == "cvc-pattern-valid" and "Mobile Phone Number" in error_message:
        return "Phone number format is incorrect or missing.  It should follow international format: +255XXXXXXXXX or 0XXXXXXXXXX."
    # If no specific match, use the general processing
    return parse_error_details(error_message, None)