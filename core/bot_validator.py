# core/bot_validator.py
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
import logging
import re
import chardet
from .models import CustomerError, CleanEntry

logger = logging.getLogger(__name__)

class BOTValidator:
    def process_xml_pair(self, customer_content, bot_content, batch=None):
        """
        Process customer XML and BOT report to generate clean XML and corrections.
        customer_content: bytes (source XML)
        bot_content: bytes (report XML or TXT)
        batch: BatchHistory instance
        Returns: (clean_xml_bytes, corrections_dict)
        """
        try:
            # Detect encoding using chardet
            customer_result = chardet.detect(customer_content)
            bot_result = chardet.detect(bot_content)
            
            customer_encoding = customer_result['encoding'] if customer_result['encoding'] else 'utf-8'
            bot_encoding = bot_result['encoding'] if bot_result['encoding'] else 'utf-8'
            
            try:
                customer_xml_str = customer_content.decode(customer_encoding)
                logger.debug(f"Customer XML decoded as {customer_encoding}")
            except UnicodeDecodeError:
                customer_xml_str = customer_content.decode('utf-8', errors='ignore')
                logger.warning("Customer XML decoded with UTF-8 ignore fallback")

            try:
                bot_xml_str = bot_content.decode(bot_encoding)
                logger.debug(f"BOT report decoded as {bot_encoding}")
            except UnicodeDecodeError:
                bot_xml_str = bot_content.decode('utf-8', errors='ignore')
                logger.warning("BOT report decoded with UTF-8 ignore fallback")

            # Log first few characters of decoded content for debugging
            logger.debug(f"Customer XML first 100 chars: {customer_xml_str[:100]}")
            logger.debug(f"BOT report first 100 chars: {bot_xml_str[:100]}")

            # Strip XML declaration to avoid encoding mismatches
            xml_decl_pattern = re.compile(r'<\?xml[^>]+?\?>')
            customer_xml_str = xml_decl_pattern.sub('', customer_xml_str).strip()
            bot_xml_str = xml_decl_pattern.sub('', bot_xml_str).strip()

            # Parse XML
            try:
                customer_tree = ET.parse(StringIO(customer_xml_str))
                customer_root = customer_tree.getroot()
                logger.debug(f"Customer XML parsed successfully. Root tag: {customer_root.tag}")
                # Log the structure of the XML up to 2 levels deep
                child_tags = []
                for child in customer_root:
                    child_tags.append(child.tag)
                    for grandchild in child:
                        child_tags.append(f"{child.tag}/{grandchild.tag}")
                logger.debug(f"Customer XML structure (up to 2 levels): {child_tags}")
            except ET.ParseError as e:
                logger.error(f"Customer XML parsing error: {str(e)}")
                return None, {'error': f'XML parsing error in source file: {str(e)}'}

            try:
                bot_tree = ET.parse(StringIO(bot_xml_str))
                bot_root = bot_tree.getroot()
                logger.debug(f"BOT report XML parsed successfully. Root tag: {bot_root.tag}")
                # Log the structure of the BOT report up to 3 levels deep
                bot_child_tags = []
                for child in bot_root:
                    bot_child_tags.append(child.tag)
                    for grandchild in child:
                        bot_child_tags.append(f"{child.tag}/{grandchild.tag}")
                        for greatgrandchild in grandchild:
                            bot_child_tags.append(f"{child.tag}/{grandchild.tag}/{greatgrandchild.tag}")
                logger.debug(f"BOT report structure (up to 3 levels): {bot_child_tags}")
            except ET.ParseError as e:
                logger.error(f"BOT report XML parsing error: {str(e)}")
                encodings = ['utf-16', 'utf-16-le', 'utf-16-be', 'latin-1']
                for enc in encodings:
                    try:
                        bot_xml_str = bot_content.decode(enc)
                        bot_xml_str = xml_decl_pattern.sub('', bot_xml_str).strip()
                        bot_tree = ET.parse(StringIO(bot_xml_str))
                        bot_root = bot_tree.getroot()
                        logger.debug(f"BOT report parsed successfully with {enc} fallback")
                        bot_child_tags = [child.tag for child in bot_root]
                        logger.debug(f"BOT report root children: {bot_child_tags}")
                        break
                    except (UnicodeDecodeError, ET.ParseError):
                        continue
                else:
                    return None, {'error': f'XML parsing error in report file: {str(e)}'}

            # Log the raw XML of the Commands section in report.xml (no namespace)
            report_commands = bot_root.find('.//Commands')
            if report_commands is not None:
                report_commands_xml = ET.tostring(report_commands, encoding='unicode')
                logger.debug(f"Raw XML of Commands in report.xml: {report_commands_xml[:1000]}")  # Limit to 1000 chars
            else:
                logger.debug("No Commands element found in report.xml")

            # Initialize corrections
            corrections = {
                'total_input_commands': 0,
                'total_clean_commands': 0,
                'clean_identifiers': [],
                'error': None
            }

            # Handle XML namespace for customer XML only
            namespaces = {
                'batch': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'
            }
            # Register the namespace
            ET.register_namespace('batch', 'http://cb4.creditinfosolutions.com/BatchUploader/Batch')

            # Find the Commands element in customer XML
            commands_elem = customer_root.find('.//batch:Commands', namespaces)
            if commands_elem is not None:
                # Log the children of Commands
                commands_children = [child.tag for child in commands_elem]
                logger.debug(f"Children of Commands element: {commands_children}")
                # Log the raw XML of the Commands element for debugging
                commands_xml = ET.tostring(commands_elem, encoding='unicode')
                logger.debug(f"Raw XML of Commands element: {commands_xml[:500]}")  # Limit to 500 chars for readability

                # Try different variations of the Command tag
                command_variations = [
                    ('batch:Command', './/batch:Command'),
                    ('batch:command', './/batch:command'),
                    ('batch:COMMAND', './/batch:COMMAND'),
                    ('batch:Request', './/batch:Request'),
                    ('batch:Transaction', './/batch:Transaction')
                ]
                commands = []
                command_tag_used = None
                for tag_name, tag_path in command_variations:
                    commands = commands_elem.findall(tag_path, namespaces)
                    if commands:
                        command_tag_used = tag_name
                        logger.debug(f"Found commands using tag: {tag_name}")
                        break

                # If no specific tag is found, try any direct children of Commands
                if not commands:
                    commands = [child for child in commands_elem if child.tag.startswith('{http://cb4.creditinfosolutions.com/BatchUploader/Batch}')]
                    if commands:
                        command_tag_used = "direct children of Commands"
                        logger.debug(f"Found commands as direct children of Commands: {[child.tag for child in commands]}")
            else:
                logger.warning("No Commands element found in customer XML")
                commands = []
                command_tag_used = None

            corrections['total_input_commands'] = len(commands)
            if corrections['total_input_commands'] == 0:
                logger.warning(f"No command elements found in customer XML under Commands element")
                CustomerError.objects.create(
                    batch=batch,
                    xml_file_name=batch.batch_identifier if batch else 'unknown_batch',
                    identifier='N/A',
                    customer_name='',
                    customer_code='',
                    account_number='',
                    amount=0,
                    national_id='',
                    phone='',
                    error_code='NO_COMMANDS',
                    message='No command elements found in source XML',
                    uploaded_by=batch.uploaded_by if batch else None,
                    status='pending',
                    severity='error'
                )
                logger.debug(f"Corrections: {corrections}")
                return None, corrections

            logger.debug(f"Found {len(commands)} commands using tag: {command_tag_used}")

            # Extract all identifiers from report.xml for debugging (no namespace)
            report_identifiers = []
            result_elements = bot_root.findall('.//Commands/Command')

            for result in result_elements:
                identifier_attr = result.get('identifier')
                if identifier_attr is not None:
                    report_identifiers.append(identifier_attr.strip())
            logger.debug(f"Identifiers found in report.xml: {report_identifiers}")

            # Process XML
            clean_commands = []
            for command in commands:
                # Extract Identifier from the Command attribute (not StorHeader)
                identifier = command.get('identifier', '').strip()
                logger.debug(f"Extracted identifier for command: {identifier}")

                # Extract other fields from Instalment and ConnectedSubject
                instalment = command.find('.//batch:Instalment', namespaces)
                connected_subject = command.find('.//batch:ConnectedSubject', namespaces)
                company = connected_subject.find('.//batch:Company', namespaces) if connected_subject is not None else None

                # Extract fields with defaults
                customer_name = ''
                customer_code = ''
                account_number = ''
                amount = 0
                national_id = ''
                phone = ''

                if company is not None:
                    customer_name = company.find('batch:CompanyData/batch:TradeName', namespaces).text if company.find('batch:CompanyData/batch:TradeName', namespaces) is not None else ''
                    customer_code = company.find('batch:CustomerCode', namespaces).text if company.find('batch:CustomerCode', namespaces) is not None else ''
                    phone = company.find('batch:ContactsCompany/batch:CellularPhone', namespaces).text if company.find('batch:ContactsCompany/batch:CellularPhone', namespaces) is not None else ''
                    national_id = company.find('batch:CompanyData/batch:RegistrationNumber', namespaces).text if company.find('batch:CompanyData/batch:RegistrationNumber', namespaces) is not None else ''

                if instalment is not None:
                    amount = instalment.find('batch:TotalLoanAmount', namespaces).text if instalment.find('batch:TotalLoanAmount', namespaces) is not None else 0
                    # Account number might not be present; set to empty if not found
                    account_number = instalment.find('batch:AccountNumber', namespaces).text if instalment.find('batch:AccountNumber', namespaces) is not None else ''

                # Find the matching Command in report.xml (no namespace)
                result = bot_root.find(f".//Commands/Command[@identifier='{identifier}']")

                if result is not None:
                    # Log the Result element for debugging
                    result_xml = ET.tostring(result, encoding='unicode')
                    logger.debug(f"Result for identifier {identifier}: {result_xml[:200]}")  # Limit to 200 chars

                    # Try different paths for ResultCode (no namespace on Lookups)
                    result_code = None
                    # Path 1: Lookups.ResultCode
                    result_code_elem = result.find('.//Lookups.ResultCode')
                    if result_code_elem is not None:
                        result_code = result_code_elem.text
                    # Path 2: Lookups/ResultCode
                    if result_code is None:
                        lookups = result.find('.//Lookups')
                        if lookups is not None:
                            result_code_elem = lookups.find('ResultCode')
                            result_code = result_code_elem.text if result_code_elem is not None else None

                    result_code = result_code if result_code is not None else 'UNKNOWN'
                    logger.debug(f"ResultCode for identifier {identifier}: {result_code}")

                    # Check for ResultCode.OK (case-insensitive)
                    if result_code and result_code.lower() == 'resultcode.ok':
                        clean_commands.append(command)
                        corrections['clean_identifiers'].append(identifier)
                        # Store clean entry in CleanEntry model
                        CleanEntry.objects.create(
                            identifier=identifier,
                            customer_name=customer_name,
                            customer_code=customer_code,
                            account_number=account_number,
                            amount=float(amount),
                            national_id=national_id,
                            batch_identifier=batch.batch_identifier if batch else 'unknown_batch',
                            status='ok',
                            xml_file_name=batch.batch_identifier if batch else 'unknown_batch'
                        )
                    else:
                        error_message = result.find('.//ErrorMessage').text if result.find('.//ErrorMessage') is not None else 'Unknown error'
                        if error_message is None:
                            error_message = f"ResultCode {result_code} is not OK"
                        CustomerError.objects.create(
                            batch=batch,
                            xml_file_name=batch.batch_identifier if batch else 'unknown_batch',
                            identifier=identifier,
                            customer_name=customer_name,
                            customer_code=customer_code,
                            account_number=account_number,
                            amount=float(amount),
                            national_id=national_id,
                            phone=phone,
                            error_code=result_code,
                            message=error_message,
                            uploaded_by=batch.uploaded_by if batch else None,
                            status='pending',
                            severity='error'
                        )
                else:
                    logger.debug(f"No Result found in report.xml for identifier: {identifier}")
                    CustomerError.objects.create(
                        batch=batch,
                        xml_file_name=batch.batch_identifier if batch else 'unknown_batch',
                        identifier=identifier,
                        customer_name=customer_name,
                        customer_code=customer_code,
                        account_number=account_number,
                        amount=float(amount),
                        national_id=national_id,
                        phone=phone,
                        error_code='NO_RESULT',
                        message='No matching result found in BOT report',
                        uploaded_by=batch.uploaded_by if batch else None,
                        status='pending',
                        severity='error'
                    )

            corrections['total_clean_commands'] = len(clean_commands)
            logger.debug(f"Corrections: {corrections}")

            # Generate clean XML
            if clean_commands:
                clean_root = ET.Element(customer_root.tag, attrib=customer_root.attrib)
                for command in clean_commands:
                    clean_root.append(command)
                clean_tree = ET.ElementTree(clean_root)
                output = BytesIO()
                clean_tree.write(output, encoding='utf-8', xml_declaration=True)
                clean_xml = output.getvalue()
                return clean_xml, corrections
            else:
                logger.debug("No clean commands found to generate clean XML")
                return None, corrections

        except Exception as e:
            logger.error(f"Unexpected error in process_xml_pair: {str(e)}")
            return None, {'error': str(e)}