from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET
from .validation_config import validation_dict, validation_dict_by_code

class BOTXMLValidator:
    def __init__(self):
        self.errors = []
        self.ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}

    def get_lookup_value(self, lookup_code: str, value_code: str) -> bool:
        """Check if a value exists in a lookup table"""
        if lookup_code in validation_dict['lookup_tables']:
            lookup_table = validation_dict['lookup_tables'][lookup_code]
            return value_code in lookup_table['values']
        return False

    def validate_instalment(self, instalment, identifier):
        """Validate Instalment section based on BOT format"""
        if instalment is None:
            return
            
        required_fields = {
            'InstalmentCount': ('int', None),
            'InstalmentType': ('lookup', 'InstallmentType'),
            'OutstandingAmount': ('decimal', None),
            'PeriodicityOfPayments': ('lookup', 'PeriodicityOfPayments'),
            'TypeOfInstalmentLoan': ('lookup', 'TypeOfInstalmentLoan'),
            'CurrencyOfLoan': ('lookup', 'Currency'),
            'EconomicSector': ('lookup', 'economic_sectors'),
            'TotalLoanAmount': ('decimal', None)
        }

        for field, (field_type, lookup_code) in required_fields.items():
            elem = instalment.find(f'ns:{field}', self.ns)
            if elem is None or not elem.text:
                self.errors.append(f"Missing {field} in Command {identifier}")
                continue

            # Validate lookup values
            if field_type == 'lookup' and lookup_code:
                value = elem.text
                if not value.startswith(f"{lookup_code}."):
                    self.errors.append(f"Invalid {field} format in Command {identifier}")

    def validate_company_data(self, company_data, identifier):
        """Validate CompanyData section"""
        if company_data is None:
            return
            
        required_fields = {
            'EstablishmentDate': ('datetime', None),
            'LegalForm': ('lookup', 'LegalForm'),
            'RegistrationNumber': ('string', None),
            'TradeName': ('string', None),
            'NegativeStatusOfClient': ('lookup', 'NegativeStatusOfClient'),
            'NumberOfEmployees': ('int', None),
            'RegistrationCountry': ('lookup', 'CountryCode'),
            'TaxIdentificationNumber': ('string', None)
        }

        for field, (field_type, lookup_code) in required_fields.items():
            elem = company_data.find(f'ns:{field}', self.ns)
            if elem is None or not elem.text:
                self.errors.append(f"Missing {field} in Command {identifier}")
                continue

            if field_type == 'lookup' and lookup_code:
                value = elem.text
                if not value.startswith(f"{lookup_code}."):
                    self.errors.append(f"Invalid {field} format in Command {identifier}")

    def validate_command(self, command, identifier):
        """Validate full StorInstalment command structure"""
        stor_instalment = command.find('.//ns:Cis.CB4.Projects.TZ.BOT.Body.Products.StorInstalment', self.ns)
        if stor_instalment is None:
            self.errors.append(f"Invalid command structure in Command {identifier}")
            return

        # Validate Instalment section
        instalment = stor_instalment.find('ns:Instalment', self.ns)
        if instalment is not None:
            self.validate_instalment(instalment, identifier)

            # Validate ConnectedSubject
            connected_subject = instalment.find('.//ns:ConnectedSubject', self.ns)
            if connected_subject is not None:
                company = connected_subject.find('.//ns:Company', self.ns)
                if company is not None:
                    company_data = company.find('ns:CompanyData', self.ns)
                    self.validate_company_data(company_data, identifier)

                    # Validate required Company elements
                    customer_code = company.findtext('ns:CustomerCode', '', self.ns)
                    if not customer_code:
                        self.errors.append(f"Missing CustomerCode in Command {identifier}")

        # Validate StorHeader
        header = stor_instalment.find('ns:StorHeader', self.ns)
        if header is None:
            self.errors.append(f"Missing StorHeader in Command {identifier}")

    def validate_connected_subject(self, subject, identifier):
        """Validate ConnectedSubject section"""
        if subject is None:
            return

        company = subject.find('.//ns:Company', self.ns)
        if company is not None:
            # Validate CompanyData
            company_data = company.find('ns:CompanyData', self.ns)
            if company_data is not None:
                required_fields = {
                    'EstablishmentDate': ('datetime', None),
                    'LegalForm': ('str', 'D05'),
                    'RegistrationNumber': ('str', None),
                    'TradeName': ('str', None)
                }

                for field, (field_type, lookup_code) in required_fields.items():
                    elem = company_data.find(f'ns:{field}', self.ns)
                    if elem is None or not elem.text:
                        self.errors.append(f"Missing {field} in Command {identifier}")

            # Validate CustomerCode
            customer_code = company.findtext('ns:CustomerCode', '', self.ns)
            if not customer_code:
                self.errors.append(f"Missing CustomerCode in Command {identifier}")

    def validate_economic_sector(self, command, identifier):
        """Validate Economic Sector exists and is properly formatted"""
        # Check in both possible locations
        sector = command.find('.//ns:EconomicSector', self.ns)
        if sector is None:
            sector = command.find('.//ns:CompanyData/ns:EconomicSector', self.ns)
            
        if sector is None or not sector.text:
            self.errors.append(f"Missing Economic Sector in Command {identifier}")
            return False
        return True

    def validate_phone_number(self, command, identifier):
        """Validate Phone Number exists"""
        phone = command.find('.//ns:ContactsCompany/ns:CellularPhone', self.ns)
        if phone is None or not phone.text or not phone.text.strip():
            self.errors.append(f"Missing Phone Number in Command {identifier}")
            return False
        return True

    def validate_xml_file(self, xml_file_path: str) -> dict:
        """Validate XML file and return precise error count"""
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Reset errors list
            self.errors = []
            
            # Track error counts
            error_counts = {
                'economic_sector': 0,
                'phone_number': 0,
                'total': 0
            }
            
            # Process each Command
            for command in root.findall('.//ns:Command', self.ns):
                identifier = command.get('identifier', '')
                
                # Check Economic Sector
                if not self.validate_economic_sector(command, identifier):
                    error_counts['economic_sector'] += 1
                
                # Check Phone Number
                if not self.validate_phone_number(command, identifier):
                    error_counts['phone_number'] += 1

            error_counts['total'] = len(self.errors)
            
            return {
                'is_valid': len(self.errors) == 0,
                'errors': self.errors,
                'error_counts': error_counts,
                'message': ("File is valid and ready for BOT upload" 
                          if len(self.errors) == 0 
                          else f"Found {len(self.errors)} validation errors that must be corrected")
            }

        except ET.ParseError as e:
            self.errors.append(f"XML Parse Error: {str(e)}")
            return {
                'is_valid': False,
                'errors': self.errors,
                'error_counts': {'total': 1},
                'message': f"Invalid XML structure: {str(e)}"
            }

    def validate_bot_specific_fields(self, command, identifier):
        """Validate BOT-specific required fields"""
        company = command.find('.//ns:Company', self.ns)
        if company is None:
            return
            
        company_data = company.find('.//ns:CompanyData', self.ns)
        if company_data is not None:
            # BOT required fields
            bot_required = [
                'EstablishmentDate',
                'NegativeStatusOfClient',
                'NumberOfEmployees',
                'RegistrationCountry',
                'TaxIdentificationNumber'
            ]
            
            for field in bot_required:
                elem = company_data.find(f'ns:{field}', self.ns)
                if elem is None:
                    self.errors.append(f"Missing required field {field} in CompanyData for Command {identifier}")

    def validate_instalment_data(self, command, identifier):
        """Validate Instalment specific fields"""
        instalment = command.find('.//ns:Instalment', self.ns)
        if instalment is not None:
            required_fields = [
                'InstalmentCount',
                'InstalmentType',
                'OutstandingAmount',
                'PeriodicityOfPayments',
                'TypeOfInstalmentLoan'
            ]
            
            for field in required_fields:
                elem = instalment.find(f'ns:{field}', self.ns)
                if elem is None or not elem.text or not elem.text.strip():
                    self.errors.append(f"Missing {field} in Command {identifier}")

    def validate_company_data_completeness(self, company_data, identifier):
        """Validate CompanyData has all required BOT fields"""
        if company_data is None:
            return
            
        required_bot_fields = [
            'EstablishmentDate',
            'NegativeStatusOfClient', 
            'NumberOfEmployees',
            'RegistrationCountry',
            'TaxIdentificationNumber'
        ]
        
        missing_fields = []
        for field in required_bot_fields:
            elem = company_data.find(f'ns:{field}', self.ns)
            if elem is None:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(
                f"CompanyData incomplete in Command {identifier}. "
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    def validate_stor_instalment(self, command, identifier):
        """Validate StorInstalment specific structure"""
        instalment = command.find('.//ns:Instalment', self.ns)
        if instalment is None:
            return
            
        required_fields = {
            'InstalmentCount': int,
            'InstalmentType': str,
            'OutstandingAmount': float,
            'PeriodicityOfPayments': str,
            'TypeOfInstalmentLoan': str,
            'CurrencyOfLoan': str,
            'TotalLoanAmount': float
        }
        
        for field, field_type in required_fields.items():
            elem = instalment.find(f'ns:{field}', self.ns)
            if elem is None or not elem.text or not elem.text.strip():
                self.errors.append(f"Missing {field} in Command {identifier}")
                continue
                
            # Validate numeric fields
            if field_type in (int, float) and elem.text:
                try:
                    field_type(elem.text.replace('.0000', ''))
                except ValueError:
                    self.errors.append(f"Invalid {field} value in Command {identifier}: {elem.text}")

    def validate_command_structure(self, command, identifier):
        """Validate complete command structure against BOT format"""
        stor_instalment = command.find('.//ns:Cis.CB4.Projects.TZ.BOT.Body.Products.StorInstalment', self.ns)
        if stor_instalment is None:
            self.errors.append(f"Invalid command structure in Command {identifier}")
            return False

        required_sections = {
            'Instalment': {
                'required_fields': [
                    'InstalmentCount',
                    'InstalmentType',
                    'OutstandingAmount',
                    'OutstandingInstalmentCount',
                    'OverdueInstalmentCount',
                    'PeriodicityOfPayments',
                    'StandardInstalmentAmount',
                    'TypeOfInstalmentLoan',
                    'CurrencyOfLoan',
                    'EconomicSector',
                    'NegativeStatusOfLoan',
                    'PastDueAmount',
                    'PhaseOfLoan',
                    'RescheduledLoan',
                    'TotalLoanAmount'
                ],
                'nested_sections': {
                    'Collateral': ['CollateralType', 'CollateralValue'],
                    'ContractDates': ['ExpectedEnd', 'RealEnd', 'Start'],
                }
            },
            'ConnectedSubject': {
                'Company': {
                    'required_fields': [
                        'CustomerCode'
                    ],
                    'nested_sections': {
                        'CompanyData': [
                            'EstablishmentDate',
                            'LegalForm',
                            'RegistrationNumber',
                            'TradeName'
                        ],
                        'AddressesCompany': {
                            'Registration': [
                                'Country',
                                'District',
                                'Region'
                            ]
                        },
                        'ContactsCompany': [
                            'CellularPhone'
                        ]
                    }
                }
            },
            'StorHeader': [
                'Source',
                'StoreTo',
                'Identifier'
            ]
        }

        # Process command sections
        instalment = stor_instalment.find('ns:Instalment', self.ns)
        if instalment is None:
            self.errors.append(f"Missing Instalment section in Command {identifier}")
            return False

        # Validate all required fields
        for field in required_sections['Instalment']['required_fields']:
            elem = instalment.find(f'ns:{field}', self.ns)
            if elem is None or not elem.text:
                self.errors.append(f"Missing {field} in Command {identifier}")

        # Validate nested sections
        connected_subject = instalment.find('.//ns:ConnectedSubject', self.ns)
        if connected_subject is not None:
            company = connected_subject.find('.//ns:Company', self.ns)
            if company is not None:
                # Check CompanyData
                company_data = company.find('ns:CompanyData', self.ns)
                if company_data is not None:
                    for field in required_sections['ConnectedSubject']['Company']['nested_sections']['CompanyData']:
                        elem = company_data.find(f'ns:{field}', self.ns)
                        if elem is None or not elem.text:
                            self.errors.append(f"Missing {field} in Command {identifier}")

                # Check ContactsCompany
                contacts = company.find('ns:ContactsCompany', self.ns)
                if contacts is not None:
                    phone = contacts.find('ns:CellularPhone', self.ns)
                    if phone is None or not phone.text:
                        self.errors.append(f"Missing Phone Number in Command {identifier}")

        return len(self.errors) == 0

    def validate_section(self, section, section_config, identifier, parent_path=''):
        """Validate a section of the XML against its configuration"""
        if section is None:
            return [f"Missing section at {parent_path} in Command {identifier}"]
            
        errors = []
        
        # Validate required fields
        for field_name, field_config in section_config.get('required_fields', {}).items():
            field = section.find(f'ns:{field_name}', self.ns)
            
            # Check field exists and has content
            if field is None or not field.text:
                errors.append(f"Missing {field_name} in Command {identifier}")
                continue
                
            # Validate field value if specified
            if 'value' in field_config and field.text != field_config['value']:
                errors.append(f"Invalid {field_name} value in Command {identifier}")
                
        # Validate nested sections
        for nested_name, nested_config in section_config.get('nested_sections', {}).items():
            nested_path = f"{parent_path}/{nested_name}" if parent_path else nested_name
            nested = section.find(f'ns:{nested_name}', self.ns)
            errors.extend(self.validate_section(nested, nested_config, identifier, nested_path))
            
        return errors