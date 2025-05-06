import xml.etree.ElementTree as ET
import re

VALIDATION_RULES = {
    # Base currency codes dictionary
    "currency_codes": {
        "by_id": {
            # All existing currency codes from your dictionary
            1: {"code": "AED", "description": "United Arab Emirates dirham"},
            2: {"code": "AFN", "description": "Afghan afghani"},
            3: {"code": "ALL", "description": "Albanian lek"},
            4: {"code": "AMD", "description": "Armenian dram"},
            5: {"code": "ANG", "description": "Netherlands Antillean guilder"},
            6: {"code": "AOA", "description": "Angolan Kwanza"},
            7: {"code": "ARS", "description": "Argentine peso"},
            8: {"code": "AUD", "description": "Australian dollar"},
            9: {"code": "AWG", "description": "Aruban guilder"},
            10: {"code": "AZN", "description": "Azerbaijani manat"},
            11: {"code": "BAM", "description": "Bosnia and Herzegovina konvertibilna marka"},
            12: {"code": "BBD", "description": "Barbados dollar"},
            13: {"code": "BDT", "description": "Bangladeshi taka"},
            14: {"code": "BGN", "description": "Bulgarian lev"},
            15: {"code": "BHD", "description": "Bahraini dinar"},
            16: {"code": "BIF", "description": "Burundian franc"},
            17: {"code": "BMD", "description": "Bermudian dollar"},
            18: {"code": "BND", "description": "Brunei dollar"},
            19: {"code": "BOB", "description": "Boliviano"},
            20: {"code": "BOV", "description": "Bolivian Mvdol (funds code)"},
            21: {"code": "BRL", "description": "Brazilian real"},
            22: {"code": "BSD", "description": "Bahamian dollar"},
            23: {"code": "BTN", "description": "Bhutan Ngultrum"},
            24: {"code": "BWP", "description": "Botswana pula"},
            25: {"code": "BYR", "description": "Belarusian ruble"},
            26: {"code": "BZD", "description": "Belize dollar"},
            27: {"code": "CAD", "description": "Canadian dollar"},
            28: {"code": "CDF", "description": "Franc Congolais"},
            29: {"code": "CHE", "description": "WIR Bank (complementary currency) (Switzerland)"},
            30: {"code": "CHF", "description": "Swiss franc"},
            31: {"code": "CHW", "description": "WIR Bank (complementary currency) (Switzerland)"},
            32: {"code": "CLF", "description": "Unidad de Fomento (funds code) Chile"},
            33: {"code": "CLP", "description": "Chilean peso"},
            34: {"code": "CNY", "description": "Chinese Yuan"},
            35: {"code": "COP", "description": "Colombian peso"},
            36: {"code": "COU", "description": "Colombian Unidad de Valor Real"},
            37: {"code": "CRC", "description": "Costa Rican colon"},
            38: {"code": "CUC", "description": "Cuban convertible peso"},
            39: {"code": "CUP", "description": "Cuban peso"},
            40: {"code": "CVE", "description": "Cape Verde escudo"},
            41: {"code": "CZK", "description": "Czech Koruna"},
            42: {"code": "DJF", "description": "Djiboutian franc"},
            43: {"code": "DKK", "description": "Danish krone"},
            44: {"code": "DOP", "description": "Dominican peso"},
            45: {"code": "DZD", "description": "Algerian dinar"},
            46: {"code": "EEK", "description": "Estonian Kroon"},
            47: {"code": "EGP", "description": "Egyptian pound"},
            48: {"code": "ERN", "description": "Eritrean nakfa"},
            49: {"code": "ETB", "description": "Ethiopian birr"},
            50: {"code": "EUR", "description": "Euro"},
            51: {"code": "FJD", "description": "Fiji dollar"},
            52: {"code": "FKP", "description": "Falkland Islands pound"},
            53: {"code": "GBP", "description": "Pound sterling"},
            54: {"code": "GEL", "description": "Georgian lari"},
            55: {"code": "GHS", "description": "Ghana Cedi"},
            56: {"code": "GIP", "description": "Gibraltar pound"},
            57: {"code": "GMD", "description": "Gambian Dalasi"},
            58: {"code": "GNF", "description": "Guinean franc"},
            59: {"code": "GTQ", "description": "Guatemalan quetzal"},
            60: {"code": "GYD", "description": "Guyanese dollar"},
            61: {"code": "HKD", "description": "Hong Kong dollar"},
            62: {"code": "HNL", "description": "Honduran lempira"},
            63: {"code": "HRK", "description": "Croatian kuna"},
            64: {"code": "HTG", "description": "Haitian gourde"},
            65: {"code": "HUF", "description": "Hungarian Forint"},
            66: {"code": "IDR", "description": "Indonesia Rupiah"},
            67: {"code": "ILS", "description": "Israeli new sheqel"},
            68: {"code": "INR", "description": "Indian rupee"},
            69: {"code": "IQD", "description": "Iraqi dinar"},
            70: {"code": "IRR", "description": "Iranian rial"},
            71: {"code": "ISK", "description": "Icelandic króna"},
            72: {"code": "JMD", "description": "Jamaican dollar"},
            73: {"code": "JOD", "description": "Jordanian dinar"},
            74: {"code": "JPY", "description": "Japanese yen"},
            75: {"code": "KES", "description": "Kenyan shilling"},
            76: {"code": "KGS", "description": "Kyrgyzstani som"},
            77: {"code": "KHR", "description": "Cambodian riel"},
            78: {"code": "KMF", "description": "Comoro franc"},
            79: {"code": "KPW", "description": "North Korean won"},
            80: {"code": "KRW", "description": "South Korean won"},
            81: {"code": "KWD", "description": "Kuwaiti dinar"},
            82: {"code": "KYD", "description": "Cayman Islands dollar"},
            83: {"code": "KZT", "description": "Kazakhstan Tenge"},
            84: {"code": "LAK", "description": "Lao kip"},
            85: {"code": "LBP", "description": "Lebanese pound"},
            86: {"code": "LKR", "description": "Sri Lanka rupee"},
            87: {"code": "LRD", "description": "Liberian dollar"},
            88: {"code": "LSL", "description": "Lesotho loti"},
            89: {"code": "LTL", "description": "Lithuanian litas"},
            90: {"code": "LVL", "description": "Latvian lats"},
            91: {"code": "LYD", "description": "Libyan dinar"},
            92: {"code": "MAD", "description": "Moroccan dirham"},
            93: {"code": "MDL", "description": "Moldovan leu"},
            94: {"code": "MGA", "description": "Malagasy ariary"},
            95: {"code": "MKD", "description": "Macedonian Denar"},
            96: {"code": "MMK", "description": "Myanmar Kyat"},
            97: {"code": "MNT", "description": "Mongolian Tugrik"},
            98: {"code": "MOP", "description": "Macanese pataca"},
            99: {"code": "MRO", "description": "Mauritania Ouguiya"},
            100: {"code": "MUR", "description": "Mauritian rupee"},
            101: {"code": "MVR", "description": "Maldives Rufiyaa"},
            102: {"code": "MWK", "description": "Malawian kwacha"},
            103: {"code": "MXN", "description": "Mexican peso"},
            104: {"code": "MXV", "description": "Mexican Unidad de Inversion (UDI) (funds code) Mexico"},
            105: {"code": "MYR", "description": "Malaysian ringgit"},
            106: {"code": "MZN", "description": "Mozambican metical"},
            107: {"code": "NAD", "description": "Namibian dollar"},
            108: {"code": "NGN", "description": "Nigerian Naira"},
            109: {"code": "NIO", "description": "Nicaraguan Cordoba oro"},
            110: {"code": "NOK", "description": "Norwegian krone"},
            111: {"code": "NPR", "description": "Nepalese rupee"},
            112: {"code": "NZD", "description": "New Zealand dollar"},
            113: {"code": "OMR", "description": "Omani Rial"},
            114: {"code": "PAB", "description": "Panamanian balboa"},
            115: {"code": "PEN", "description": "Peruvian nuevo sol"},
            116: {"code": "PGK", "description": "Papua New Guinean kina"},
            117: {"code": "PHP", "description": "Philippine peso"},
            118: {"code": "PKR", "description": "Pakistani rupee"},
            119: {"code": "PLN", "description": "Polish Zloty"},
            120: {"code": "PYG", "description": "Paraguayan guaraní"},
            121: {"code": "QAR", "description": "Qatari rial"},
            122: {"code": "RON", "description": "Romanian new leu"},
            123: {"code": "RSD", "description": "Serbian dinar"},
            124: {"code": "RUB", "description": "Russian rouble"},
            125: {"code": "RWF", "description": "Rwandan franc"},
            126: {"code": "SAR", "description": "Saudi riyal"},
            127: {"code": "SBD", "description": "Solomon Islands dollar"},
            128: {"code": "SCR", "description": "Seychelles rupee"},
            129: {"code": "SDG", "description": "Sudanese pound"},
            130: {"code": "SEK", "description": "Swedish krona/kronor"},
            131: {"code": "SGD", "description": "Singapore dollar"},
            132: {"code": "SHP", "description": "Saint Helena pound"},
            133: {"code": "SLL", "description": "Sierra Leonean leone"},
            134: {"code": "SOS", "description": "Somali shilling"},
            135: {"code": "SRD", "description": "Surinamese dollar"},
            136: {"code": "STD", "description": "São Tomé and Príncipe dobra"},
            137: {"code": "SYP", "description": "Syrian pound"},
            138: {"code": "SZL", "description": "Swazi Lilangeni"},
            139: {"code": "THB", "description": "Thai Baht"},
            140: {"code": "TJS", "description": "Tajikistan Somoni"},
            141: {"code": "TMT", "description": "Turkmenistani manat"},
            142: {"code": "TND", "description": "Tunisian dinar"},
            143: {"code": "TOP", "description": "Tonga Pa'anga"},
            144: {"code": "TRY", "description": "Turkish lira"},
            145: {"code": "TTD", "description": "Trinidad and Tobago dollar"},
            146: {"code": "TWD", "description": "New Taiwan dollar"},
            147: {"code": "TZS", "description": "Tanzanian shilling"},
            148: {"code": "UAH", "description": "Ukrainian Hryvnia"},
            149: {"code": "UGX", "description": "Ugandan shilling"},
            150: {"code": "USD", "description": "United States dollar"},
            151: {"code": "USN", "description": "United States dollar (next day) (funds code)"},
            152: {"code": "USS", "description": "United States dollar (same day) (funds code)"},
            153: {"code": "UYU", "description": "Uruguayan Peso"},
            154: {"code": "UZS", "description": "Uzbekistan som"},
            155: {"code": "VEF", "description": "Venezuelan bolívar fuerte"},
            156: {"code": "VND", "description": "Vietnamese dong"},
            157: {"code": "VUV", "description": "Vanuatu Vatu"},
            158: {"code": "WST", "description": "Samoan tala"},
            159: {"code": "XAF", "description": "CFA franc BEAC"},
            160: {"code": "XAG", "description": "Silver (one troy ounce)"},
            161: {"code": "XAU", "description": "Gold (one troy ounce)"},
            162: {"code": "XBA", "description": "European Composite Unit (EURCO) (bond market unit)"},
            163: {"code": "XBB", "description": "European Monetary Unit (E.M.U.-6) (bond market unit)"},
            164: {"code": "XBC", "description": "European Unit of Account 9 (E.U.A.-9) (bond market unit)"},
            165: {"code": "XBD", "description": "European Unit of Account 17 (E.U.A.-17) (bond market unit)"},
            166: {"code": "XCD", "description": "East Caribbean dollar"},
            167: {"code": "XDR", "description": "Special Drawing Rights (International Monetary Fund)"},
            168: {"code": "XFU", "description": "UIC franc (special settlement currency) (International Union of Railways)"},
            169: {"code": "XOF", "description": "CFA Franc BCEAO"},
            170: {"code": "XPD", "description": "Palladium (one troy ounce)"},
            171: {"code": "XPF", "description": "CFP franc"},
            172: {"code": "XPT", "description": "Platinum (one troy ounce)"},
            173: {"code": "XTS", "description": "Testing Code"},
            174: {"code": "XXX", "description": "No currency"},
            175: {"code": "YER", "description": "Yemeni rial"},
            176: {"code": "ZAR", "description": "South African rand"},
            177: {"code": "ZMK", "description": "Zambian kwacha"},
            178: {"code": "ZWL", "description": "Zimbabwe dollar"},
            179: {"code": "SZL", "description": "ESWATINI"},
            180: {"code": "SSP", "description": "SOUTH SUDAN"}
        }
    },

    # Document validation rules
    "document_rules": {
        "national_id": {
            "pattern": r"[0-9]{8}(-[0-9]{5}){2}-[0-9]{2}",
            "example": "YYYYMMDD-00000-00000-1/2/3C",
            "description": "National ID format with checksum",
            "validation_rules": [
                "20 digits total",
                "Last digit is checksum",
                "Birth date + postal code + serial + gender/checksum"
            ]
        },
        "driving_license": {
            "mainland": {
                "pattern": r"[0-9]{10}",
                "description": "Mainland driving license"
            },
            "zanzibar": {
                "pattern": r"[Z]{1}[0-9]{9}",
                "description": "Zanzibar driving license"
            }
        },
        "passport": {
            "pattern": r"[a-zA-Z]{2}[0-9]{6}",
            "description": "Tanzanian passport format"
        },
        "voter_id": {
            "mainland": {
                "pattern": r"[0-9]{8}",
                "description": "Mainland voter ID"
            },
            "zanzibar": {
                "pattern": r"[0-9]{9}",
                "description": "Zanzibar voter ID"
            }
        },
        "zanzibar_id": {
            "pattern": r"[0-9]{9}",
            "description": "Zanzibar ID number"
        },
        "bot_license": {
            "pattern": r"[M]{1}[S]{1}[P]{1}[0-9]{5}",
            "example": "MSP2-0885",
            "description": "BOT licence number"
        },
        "tax_id": {
            "pattern": r"[0-9]{3}(-[0-9]{3}){2}",
            "description": "Tax identification number"
        }
    },

    # Contact information rules
    "contact_rules": {
        "phone": {
            "cellular": {
                "pattern": r"((\\+255[0-9]{9})|(0[0-9]{9})){1}",
                "examples": ["+255123456789", "0123456789"],
                "description": "Cellular phone number"
            },
            "fixed_line": {
                "pattern": r"((\\+255[0-9]{9})|([0-9]{7,9})){1}",
                "examples": ["+255123456789", "12345678"],
                "description": "Fixed line number"
            }
        },
        "email": {
            "pattern": r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,6}",
            "description": "Email address format"
        },
        "website": {
            "pattern": r"(http|https)\\://[a-zA-Z0-9\\-\\.]+\\.[a-zA-Z]{2,3}(:[a-zA-Z0-9]*)?/?([a-zA-Z0-9\\-\\._\\?\\,\\'\\/\\\\+&amp;%\\$#\\=~])*",
            "description": "Web page URL format"
        }
    },

    "address_rules": {
        "postal_code": {
            "pattern": r"[0-9]{5}",
            "example": "11884",
            "description": "5-digit postal code"
        }
    },

    "registration_rules": {
        "brela": {
            "mainland": {
                "pattern": r"[0-9]{1,6}",
                "example": "123456",
                "description": "BRELA registration number"
            },
            "zanzibar": {
                "pattern": r"[Z]{1}[0-9]{10}",
                "example": "Z0000019264",
                "description": "Zanzibar BRELA number"
            }
        }
    },

    "date_rules": {
        "birth_date": {
            "min_age": 18,
            "max_age": 99,
            "description": "Individual must be between 18 and 99 years old"
        },
        "establishment_date": {
            "rule": "must_be_past",
            "description": "Must be less than reporting date"
        },
        "issuance_date": {
            "rule": "must_be_past",
            "description": "Must not be greater than reporting date"
        },
        "expiration_date": {
            "rules": [
                "must_be_after_issuance",
                "must_be_after_reporting"
            ],
            "description": "Must be after issuance and reporting dates"
        }
    },

    "amount_rules": {
        "monthly_income": {
            "type": "decimal",
            "precision": 18,
            "scale": 4,
            "min": 0,
            "requires_currency": True
        },
        "monthly_expenditure": {
            "type": "decimal",
            "precision": 18,
            "scale": 4,
            "min": 0,
            "requires_currency": True
        },
        "shares_percentage": {
            "type": "decimal",
            "min": 0,
            "max": 100
        }
    },

    "text_rules": {
        "additional_info": {
            "max_length": 255,
            "type": "free_text"
        }
    },

    # Lookup tables from documentation
    "lookup_tables": {
        "D01": {  # Individual classification
            "1": "Individual",
            "2": "SoleProprietor"
        },
        "D02": {  # Relations
            "1": "No relation",
            "2": "Family"
        },
        "D03": {  # Gender
            "1": "Male",
            "2": "Female"
        },
        "D04": {  # Negative status of client
            "1": "NoNegativeStatus",
            "2": "SupervisoryOrCrisisAdministration",
            "3": "OtherCourtActionByBank",
            "4": "BankruptcyPetitionByBank",
            "5": "BankruptcyPetition",
            "6": "CourtDeclaredBankruptcy",
            "7": "Receivership",
            "8": "Liquidation",
            "9": "AssetsFrozenOrSeized",
            "10": "CustomerUntraceableOrDeceased"
        },
        "D05": {  # Legal Form
            "1": "JointLiabilityCompany",
            "2": "SpecialPartnershipCompany",
            "3": "LimitedLiabilityCompanyPublic",
            "4": "LimitedLiabilityCompanyPrivate",
            "5": "JointStockCompany",
            "6": "Cooperative",
            "7": "Foundations",
            "8": "Association",
            "9": "Other",
            "10": "Audit",
            "11": "Notary",
            "12": "Copartnership",
            "13": "NonregisteredAssociation",
            "14": "ReligiousOrganization",
            "15": "GovernmentalInstitution",
            "16": "PoliticPartyOrUnion",
            "17": "Branch",
            "18": "LegalPersonUnderPublicLaw",
            "19": "PublicInstitution"
        },
        "D07": {  # Negative status of loan
            "1": "NoNegativeStatus",
            "2": "UnauthorizedDebitBalanceOnCurrentAccount",
            "3": "Blocked",
            "4": "CancelledDueToDelayedPayments",
            "5": "InsuranceFraud",
            "6": "FraudTowardsBank",
            "7": "CreditReassignedToNewDebtor",
            "8": "AssignmentOfCreditToThirdParty",
            "9": "LoanWrittenOff",
            "10": "IncreasedRisk",
            "11": "LoanTransferredToLosses"
        },
        "D08": {  # Role of client (in the loan)
            "1": "MainDebtor",
            "1": "CoDebtor",  # Note: This appears to be a duplicate code in the document
            "2": "Guarantor"
        },
        "D09": {  # Collateral type
            "1": "Stocks",
            "2": "Deposit",
            "3": "SalaryDeposit",
            "4": "RealEstate",
            "5": "TerminalBenefits",
            "6": "Equipment",
            "7": "GovernmentSecurities",
            "8": "Gold",
            "9": "StateGuarantee",
            "10": "Other",
            "11": "MotorVehicle"
        },
        "D10": {  # Periodicity of payments
            "1": "AtTheFinalDayOfThePeriodOfContract",
            "2": "FortnightlyInstalments15Days",
            "3": "MonthlyInstalments30Days",
            "4": "BimonthlyInstalments60Days",
            "5": "QuarterlyInstalments90Days",
            "6": "FourMonthInstalments120Days",
            "7": "FiveMonthInstalments150Days",
            "8": "SixMonthInstalments180Days",
            "9": "AnnualInstalments360Days",
            "10": "IrregularInstalments"
        },
        "D11": {  # Method of payment
            "1": "CurrentAccount",
            "2": "BillOfExchange",
            "3": "BankingReceipt",
            "4": "DirectRemittance",
            "5": "AuthorizationToDirectCurrentAccountDebit"
        },
        "D12": {  # Card used in Current Month
            "1": "CardNotUsedInCurrentMonth",
            "2": "CardUsedInCurrentMonth"
        },
        "D13": {  # Phase of loan
            "1": "Existing",
            "2": "TerminatedAccordingTheContract",
            "3": "TerminatedInAdvanceCorrectly",
            "4": "TerminatedInAdvanceIncorrectly"
        },
        "D16": {  # Resolution of the dispute
            "1": "DisputeWasEligible",
            "2": "DisputeWasNotEligible"
        },
        "D17": {  # Marital status
            "1": "Single",
            "2": "Married",
            "3": "Divorced",
            "4": "Widowed"
        },
        "D18": {  # Purpose of loan
            "1": "Construct",
            "2": "Development",
            "3": "WorkingCapital",
            "4": "PurchaseOfBuilding",
            "5": "PurchaseOfPersonalConsumingProducts",
            "6": "Repair",
            "7": "SyndicatedLoan",
            "8": "Others"
        },
        "D19": {  # Type of instalments
            "1": "Fixed",
            "2": "Variable"
        },
        "D20": {  # Education
            "1": "NoEducation",
            "2": "Basic",
            "3": "Secondary",
            "4": "College",
            "5": "University",
            "6": "Other"
        },
        "D21": {  # Boolean
            "1": "True",
            "2": "False"
        },
        "D22": {  # Relation type (between subjects)
            "1": "Shareholder",
            "2": "CEO",
            "3": "COO",
            "4": "Financialdirector",
            "5": "MainAccountant",
            "6": "Topmanager",
            "7": "Middlemanager",
            "8": "Employee",
            "9": "Employer",
            "10": "Spouse",
            "11": "Other"
        },
        "D24A": {  # Type of instalment loan
            "1": "ConsumerLoan",
            "2": "BusinessLoan",
            "3": "MortgageLoan",
            "4": "LeasingFinancial",
            "5": "LeasingOperational",
            "6": "OtherInstalmentOpera"
        },
        "D24B": {  # Type of noninstalment loan
            "1": "PawnLoan",
            "2": "Overdraft",
            "3": "LineOfCreditOnCurren",
            "4": "AllowedDebitOnCurre",
            "5": "OtherNoninstalmentO"
        },
        "D24C": {  # Type of credit card
            "1": "CreditCard",
            "2": "CreditCardWithRegul",
            "3": "CreditCardOverdrafts",
            "4": "RevolvingCredit",
            "5": "OtherCreditCardOper"
        },
        "D24D": {  # Type of invoice / bill
            "1": "InvoiceForServices",
            "2": "InvoiceForGoods",
            "3": "Bill",
            "4": "OtherOneShotPayme"
        },
        "D25D": {  # Registration Number for Other than BRELA Registered Company
            "1": "TCDC",
            "2": "Ministry of Home Affairs",
            "3": "Ministry of Education, Science and Technology",
            "4": "BRELA",
            "5": "BPRA",
            "6": "TAMISEMI"
        },
        "District": {
            "name": "District",
            "values": {
                "1": {"value": "Arusha", "description": "Arusha"},
                "2": {"value": "Arumeru", "description": "Arumeru"},
                # ... previous districts ...
                "59": {"value": "Kwimba", "description": "Kwimba"},
                "60": {"value": "Kyela", "description": "Kyela"},
                "61": {"value": "Lindi", "description": "Lindi"},
                "62": {"value": "Liwale", "description": "Liwale"},
                "63": {"value": "Longido", "description": "Longido"},
                "64": {"value": "Ludewa", "description": "Ludewa"},
                "65": {"value": "Lushoto", "description": "Lushoto"},
                "66": {"value": "Mafia", "description": "Mafia"},
                "67": {"value": "Magharibi", "description": "Magharibi"},
                "68": {"value": "Makete", "description": "Makete"},
                "69": {"value": "Manyoni", "description": "Manyoni"},
                "70": {"value": "Masasi", "description": "Masasi"},
                "71": {"value": "Maswa", "description": "Maswa"},
                "72": {"value": "Mbarali", "description": "Mbarali"},
                "73": {"value": "Mbeya", "description": "Mbeya"},
                "74": {"value": "Mbinga", "description": "Mbinga"},
                "75": {"value": "Mbogwe", "description": "Mbogwe"},
                "76": {"value": "Mbozi", "description": "Mbozi"},
                "77": {"value": "Mbulu", "description": "Mbulu"},
                "78": {"value": "Meatu", "description": "Meatu"},
                "79": {"value": "Micheweni", "description": "Micheweni"},
                "80": {"value": "Missungwi", "description": "Missungwi"},
                "81": {"value": "Mjini", "description": "Mjini"},
                "82": {"value": "Mkinga", "description": "Mkinga"},
                "83": {"value": "Mkuranga", "description": "Mkuranga"},
                "84": {"value": "Monduli", "description": "Monduli"},
                "85": {"value": "Morogoro", "description": "Morogoro"},
                "86": {"value": "Moshi", "description": "Moshi"},
                "87": {"value": "Mpanda", "description": "Mpanda"},
                "88": {"value": "Mpwapwa", "description": "Mpwapwa"},
                "89": {"value": "Msalala", "description": "Msalala"},
                "90": {"value": "Mtwara", "description": "Mtwara"},
                "91": {"value": "Muheza", "description": "Muheza"},
                "92": {"value": "Muleba", "description": "Muleba"},
                "93": {"value": "Musoma", "description": "Musoma"},
                "94": {"value": "Mvomero", "description": "Mvomero"},
                "95": {"value": "Mwanga", "description": "Mwanga"},
                "96": {"value": "Nachingwea", "description": "Nachingwea"},
                "97": {"value": "Namtumbo", "description": "Namtumbo"},
                "98": {"value": "Nanyumbu", "description": "Nanyumbu"},
                "99": {"value": "Ngara", "description": "Ngara"},
                "100": {"value": "Ngorongoro", "description": "Ngorongoro"},
                "101": {"value": "Njombe", "description": "Njombe"},
                "102": {"value": "Nkasi", "description": "Nkasi"},
                "103": {"value": "Nsimbo", "description": "Nsimbo"},
                "104": {"value": "Nyamagana", "description": "Nyamagana"},
                "105": {"value": "Nyang'hwale", "description": "Nyang'hwale"},
                "106": {"value": "Nyasa", "description": "Nyasa"},
                "107": {"value": "Pangani", "description": "Pangani"},
                "108": {"value": "Rombo", "description": "Rombo"},
                "109": {"value": "Ruangwa", "description": "Ruangwa"},
                "110": {"value": "Rufiji", "description": "Rufiji"},
                "111": {"value": "Rungwe", "description": "Rungwe"},
                "112": {"value": "Same", "description": "Same"},
                "113": {"value": "Sengerema", "description": "Sengerema"},
                "114": {"value": "Serengeti", "description": "Serengeti"},
                "115": {"value": "Shinyanga", "description": "Shinyanga"},
                "116": {"value": "Siha", "description": "Siha"},
                "117": {"value": "Simanjiro", "description": "Simanjiro"},
                "118": {"value": "Singida", "description": "Singida"},
                "119": {"value": "Songea", "description": "Songea"},
                "120": {"value": "Sumbawanga", "description": "Sumbawanga"},
                "121": {"value": "Tabora", "description": "Tabora"},
                "122": {"value": "Tandahimba", "description": "Tandahimba"},
                "123": {"value": "Tanga", "description": "Tanga"},
                "124": {"value": "Tarime", "description": "Tarime"},
                "125": {"value": "Temeke", "description": "Temeke"},
                "126": {"value": "Tunduru", "description": "Tunduru"},
                "127": {"value": "Ukerewe", "description": "Ukerewe"},
                "128": {"value": "Ulanga", "description": "Ulanga"},
                "129": {"value": "Urambo", "description": "Urambo"},
                "130": {"value": "Ushetu", "description": "Ushetu"},
                "131": {"value": "Uyui", "description": "Uyui"},
                "132": {"value": "Wete", "description": "Wete"}
            }
        }
    },

    # XML structure validation
    "xml_structure": {
        "Individual": {
            "xpath": "//Cis.CB4.Projects.TZ.BOT.Body.Products.StorInstalment/Instalment/ConnectedSubject/SubjectChoice/Individual",
            "elements": {
                "CustomerCode": {
                    "description": "Customer code - unique number for a customer assigned by data provider",
                    "mandatory": True,
                    "rules": "Each data provider has to provide each customer with unique code. This code is lifetime code (permanent).",
                    "data_type": "String",
                    "length": 32,
                    "xpath": "./CustomerCode"
                },
                "PersonalData": {
                    "description": "Section with main personal data",
                    "mandatory": True,
                    "data_type": "Section",
                    "xpath": "./PersonalData",
                    "elements": {
                        "IndividualClassification": {
                            "description": "Individual or individual with trading license.",
                            "mandatory": True,
                            "rules": "See attribute table D01 for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/IndividualClassification"
                        },
                        "NegativeStatusOfClient": {
                            "description": "The most negative status.",
                            "mandatory": False,
                            "rules": "See attribute table D04 for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/NegativeStatusOfClient"
                        },
                        "FirstName": {
                            "description": "Any language",
                            "mandatory": True,
                            "data_type": "String",
                            "length": 64,
                            "xpath": "./PersonalData/FirstName"
                        },
                        "MiddleNames": {
                            "description": "Any language, can contain more names",
                            "mandatory": False,
                            "data_type": "String",
                            "length": 64,
                            "xpath": "./PersonalData/MiddleNames"
                        },
                        "LastName": {
                            "description": "Any language",
                            "mandatory": True,
                            "data_type": "String",
                            "length": 64,
                            "xpath": "./PersonalData/LastName"
                        },
                        "MaritalStatus": {
                            "description": "Marital status",
                            "mandatory": True,
                            "rules": "See attribute table D17 for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/MaritalStatus"
                        },
                        "SpouseFullName": {
                            "description": "Field can be repeated for each husband or wife name. Field should contain full name (including the middle names)",
                            "mandatory": False,
                            "data_type": "String",
                            "length": 256,
                            "xpath": "./PersonalData/SpouseFullName"
                        },
                        "Gender": {
                            "description": "Gender",
                            "mandatory": True,
                            "rules": "See attribute table D03 for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/Gender"
                        },
                        "BirthSurname": {
                            "description": "Birth surname",
                            "mandatory": False,
                            "rules": "Business rule: Mandatory for all females (Gender = Female). Otherwise optional.",
                            "data_type": "String",
                            "length": 64,
                            "xpath": "./PersonalData/BirthSurname"
                        },
                        "Nationality": {
                            "description": "The status of belonging to a particular nation.",
                            "mandatory": True,
                            "rules": "See sheet \"Country codes\" for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/Nationality"
                        },
                        "Citizenship": {
                            "description": "The status of a citizen with rights and duties.",
                            "mandatory": False,
                            "rules": "See sheet \"Country codes\" for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/Citizenship"
                        },
                        "Profession": {
                            "description": "Profession",
                            "mandatory": False,
                            "rules": "See sheet \"Profession\" for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/Profession"
                        },
                        "EmployerName": {
                            "description": "Name of employer - to be used only if employer cannot be identified fully in section RELATION",
                            "mandatory": False,
                            "data_type": "String",
                            "length": 128,
                            "xpath": "./PersonalData/EmployerName"
                        },
                        "MonthlyIncome": {
                            "description": "Combination of two fields (Decimal1804 for amount value and Lookup for currency)",
                            "mandatory": False,
                            "rules": "See sheet \"Currencies\" for lookup values\nBusiness rule: Amount can not be negative",
                            "data_type": ["Decimal1804", "Lookup"],
                            "xpath": "./PersonalData/MonthlyIncome"
                        },
                        "NumberOfChildren": {
                            "description": "Nr. of children",
                            "mandatory": False,
                            "data_type": "Int32",
                            "xpath": "./PersonalData/NumberOfChildren"
                        },
                        "NumberOfSpouses": {
                            "description": "Nr. of spouses",
                            "mandatory": False,
                            "data_type": "Int32",
                            "xpath": "./PersonalData/NumberOfSpouses"
                        },
                        "Education": {
                            "description": "Education (highest achieved)",
                            "mandatory": False,
                            "rules": "See attribute table D20 for lookup values",
                            "data_type": "Lookup",
                            "xpath": "./PersonalData/Education"
                        },
                        "MonthlyExpenditures": {
                            "description": "Combination of two fields (Decimal1804 for amount value and Lookup for currency)",
                            "mandatory": False,
                            "rules": "See sheet \"Currencies\" for lookup values\nBusiness rule: Amount can not be negative",
                            "data_type": ["Decimal1804", "Lookup"],
                            "xpath": "./PersonalData/MonthlyExpenditures"
                        },
                        "BirthData": {
                            "description": "Subsection of personal data",
                            "mandatory": True,
                            "data_type": "Subsection",
                            "xpath": "./PersonalData/BirthData",
                            "elements": {
                                "BirthDate": {
                                    "description": "Date of Birth",
                                    "mandatory": True,
                                    "rules": "Business rule: Individual must be between 18 and 99 years old!",
                                    "data_type": "DateTime",
                                    "xpath": "./PersonalData/BirthData/BirthDate"
                                },
                                "District": {
                                    "description": "District of birth, applicable only for individuals born in any Tanzanian district",
                                    "mandatory": False,
                                    "rules": "See sheet \"District\" for lookup values",
                                    "data_type": "Lookup",
                                    "xpath": "./PersonalData/BirthData/District"
                                },
                                "Country": {
                                    "description": "Country of birth",
                                    "mandatory": False,
                                    "rules": "See sheet \"Country codes\" for lookup values\nBusiness rule: Mandatory for foreigners (if Citizenship is filled and the value is not \"Tanzania\").",
                                    "data_type": "Lookup",
                                    "xpath": "./PersonalData/BirthData/Country"
                                }
                            }
                        }
                    }
                },
                "Identifications": {
                    "description": "Section with identification documents",
                    "mandatory": True,
                    "data_type": "Section",
                    "xpath": "./Identifications",
                    "elements": {
                        "DrivingLicense": {
                            "description": "Subsection of Identification",
                            "mandatory": False,
                            "rules": "Business rule: At least one identification document must be filled in",
                            "data_type": "Subsection",
                            "xpath": "./Identifications/DrivingLicense",
                            "elements": {
                                "NumberOfDrivingLicense": {
                                    "description": "Number of identification document to include both Zanzibar and Mainland Driving licence format.",
                                    "mandatory": True,
                                    "rules": "Driving license for Mainland has 10 digits.\nRegular expression: [0-9]{10}.Driving license for Zanzibar has 9 digits.\nRegular expression:[Z]{1}[0-9]{9}",
                                    "data_type": "String",
                                    "length": 16,
                                    "xpath": "./Identifications/DrivingLicense/NumberOfDrivingLicense"
                                },
                                "DateOfIssuance": {
                                    "description": "The date of issuance of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Issuance date must not be greater than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/DrivingLicense/DateOfIssuance"
                                },
                                "DateOfExpiration": {
                                    "description": "The date of expiration of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Expiration date must not be less than issuance date.\nBusiness rule: Expiration date must not be less than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/DrivingLicense/DateOfExpiration"
                                },
                                "IssuanceLocation": {
                                    "description": "The location where the ID was issued.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/DrivingLicense/IssuanceLocation"
                                },
                                "IssuedBy": {
                                    "description": "The name or organization which issued the document.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 128,
                                    "xpath": "./Identifications/DrivingLicense/IssuedBy"
                                }
                            }
                        },
                        "NationalId": {
                            "description": "Subsection of Identification",
                            "mandatory": False,
                            "rules": "Business rule: At least one identification document must be filled in",
                            "data_type": "Subsection",
                            "xpath": "./Identifications/NationalId",
                            "elements": {
                                "NumberOfNationalId": {
                                    "description": "Number of identification document",
                                    "mandatory": True,
                                    "rules": "National ID number has 20 digits where last digit is checksum, format is YYYYMMDD-00000-00000-1/2/3C\nRegular expression: [0-9]{8}(-[0-9]{5}){2}-[0-9]{2}\nBusiness rule: The first eight numerical numbers represent the year, month and day the person was born\nBusiness rule: The second set of five numerical numbers refer to the postal code of the area the person was registered for the first time\nBusiness rule: The third set of five numerical numbers, refer to the serial number of the registered person in that date, month and year of birth in the postal code area of first registration\nBusiness rule: The fourth numerical number refers to the sex of the registered person; 1 = woman, 2 = man, 3 = hermaphrodite",
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/NationalId/NumberOfNationalId"
                                },
                                "DateOfIssuance": {
                                    "description": "The date of issuance of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Issuance date must not be greater than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/NationalId/DateOfIssuance"
                                },
                                "DateOfExpiration": {
                                    "description": "The date of expiration of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Expiration date must not be less than issuance date.\nBusiness rule: Expiration date must not be less than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/NationalId/DateOfExpiration"
                                },
                                "IssuanceLocation": {
                                    "description": "The location where the ID was issued.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/NationalId/IssuanceLocation"
                                },
                                "IssuedBy": {
                                    "description": "The name or organization which issued the document.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 128,
                                    "xpath": "./Identifications/NationalId/IssuedBy"
                                }
                            }
                        },
                        "Passport": {
                            "description": "Subsection of Identification",
                            "mandatory": False,
                            "rules": "Business rule: At least one identification document must be filled in",
                            "data_type": "Subsection",
                            "xpath": "./Identifications/Passport",
                            "elements": {
                                "NumberOfPassport": {
                                    "description": "Number of identification document",
                                    "mandatory": True,
                                    "rules": "Passport number has 8 characters, format is AA000000\nRegular expression: [a-zA-Z]{2}[0-9]{6}",
                                    "data_type": "String",
                                    "length": 16,
                                    "xpath": "./Identifications/Passport/NumberOfPassport"
                                },
                                "DateOfIssuance": {
                                    "description": "The date of issuance of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Issuance date must not be greater than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/Passport/DateOfIssuance"
                                },
                                "DateOfExpiration": {
                                    "description": "The date of expiration of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Expiration date must not be less than issuance date.\nBusiness rule: Expiration date must not be less than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/Passport/DateOfExpiration"
                                },
                                "IssuanceLocation": {
                                    "description": "The location where the ID was issued.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/Passport/IssuanceLocation"
                                },
                                "IssuedBy": {
                                    "description": "The name or organization which issued the document.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 128,
                                    "xpath": "./Identifications/Passport/IssuedBy"
                                }
                            }
                        },
                        "VoterId": {
                            "description": "Subsection of Identification",
                            "mandatory": False,
                            "rules": "Business rule: At least one identification document must be filled in",
                            "data_type": "Subsection",
                            "xpath": "./Identifications/VoterId",
                            "elements": {
                                "NumberOfVoterId": {
                                    "description": "Number of identification document to include both Zanzibar and Mainland Voter ID format.",
                                    "mandatory": True,
                                    "rules": "Voter ID for Mainland has 8 digits.\nRegular expression: [0-9]{8}.Voter ID for Zanzibar has 9 digits.\nRegular expression:[0-9]{9}",
                                    "data_type": "String",
                                    "length": 16,
                                    "xpath": "./Identifications/VoterId/NumberOfVoterId"
                                },
                                "DateOfIssuance": {
                                    "description": "The date of issuance of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Issuance date must not be greater than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/VoterId/DateOfIssuance"
                                },
                                "DateOfExpiration": {
                                    "description": "The date of expiration of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Expiration date must not be less than issuance date.\nBusiness rule: Expiration date must not be less than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/VoterId/DateOfExpiration"
                                },
                                "IssuanceLocation": {
                                    "description": "The location where the ID was issued.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/VoterId/IssuanceLocation"
                                },
                                "IssuedBy": {
                                    "description": "The name or organization which issued the document.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 128,
                                    "xpath": "./Identifications/VoterId/IssuedBy"
                                }
                            }
                        },
                        "ZanzibarId": {
                            "description": "Subsection of Identification",
                            "mandatory": False,
                            "rules": "Business rule: At least one identification document must be filled in",
                            "data_type": "Subsection",
                            "xpath": "./Identifications/ZanzibarId",
                            "elements": {
                                "NumberOfZanzibarId": {
                                    "description": "Number of identification document",
                                    "mandatory": True,
                                    "rules": "Zanzibar ID number has 9 digits.\nRegular expression: [0-9]{9}",
                                    "data_type": "String",
                                    "length": 16,
                                    "xpath": "./Identifications/ZanzibarId/NumberOfZanzibarId"
                                },
                                "DateOfIssuance": {
                                    "description": "The date of issuance of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Issuance date must not be greater than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/ZanzibarId/DateOfIssuance"
                                },
                                "DateOfExpiration": {
                                    "description": "The date of expiration of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Expiration date must not be less than issuance date.\nBusiness rule: Expiration date must not be less than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/ZanzibarId/DateOfExpiration"
                                },
                                "IssuanceLocation": {
                                    "description": "The location where the ID was issued.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/ZanzibarId/IssuanceLocation"
                                },
                                "IssuedBy": {
                                    "description": "The name or organization which issued the document.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 128,
                                    "xpath": "./Identifications/ZanzibarId/IssuedBy"
                                }
                            }
                        },
                        "BotLicense": {
                            "description": "Subsection of Identification",
                            "mandatory": False,
                            "rules": "Business rule: At least one identification document must be filled in",
                            "data_type": "Subsection",
                            "xpath": "./Identifications/BotLicense",
                            "elements": {
                                "NumberOfBotLicense": {
                                    "description": "Number of identification document",
                                    "mandatory": True,
                                    "rules": "BOT license number has 8 characters, format is MSP2-0885\nRegular expression: [M]{1}[S]{1}[P]{1}[0-9]{5}",
                                    "data_type": "String",
                                    "length": 16,
                                    "xpath": "./Identifications/BotLicense/NumberOfBotLicense"
                                },
                                "DateOfIssuance": {
                                    "description": "The date of issuance of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Issuance date must not be greater than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/BotLicense/DateOfIssuance"
                                },
                                "DateOfExpiration": {
                                    "description": "The date of expiration of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Expiration date must not be less than issuance date.\nBusiness rule: Expiration date must not be less than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/BotLicense/DateOfExpiration"
                                },
                                "IssuanceLocation": {
                                    "description": "The location where the ID was issued.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/BotLicense/IssuanceLocation"
                                },
                                "IssuedBy": {
                                    "description": "The name or organization which issued the document.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 128,
                                    "xpath": "./Identifications/BotLicense/IssuedBy"
                                }
                            }
                        },
                        "TaxId": {
                            "description": "Subsection of Identification",
                            "mandatory": False,
                            "rules": "Business rule: At least one identification document must be filled in",
                            "data_type": "Subsection",
                            "xpath": "./Identifications/TaxId",
                            "elements": {
                                "NumberOfTaxId": {
                                    "description": "Number of identification document",
                                    "mandatory": True,
                                    "rules": "Tax ID number has 9 digits, format is 000-000-000\nRegular expression: [0-9]{3}(-[0-9]{3}){2}",
                                    "data_type": "String",
                                    "length": 16,
                                    "xpath": "./Identifications/TaxId/NumberOfTaxId"
                                },
                                "DateOfIssuance": {
                                    "description": "The date of issuance of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Issuance date must not be greater than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/TaxId/DateOfIssuance"
                                },
                                "DateOfExpiration": {
                                    "description": "The date of expiration of the identification document.",
                                    "mandatory": False,
                                    "rules": "Business rule: Expiration date must not be less than issuance date.\nBusiness rule: Expiration date must not be less than reporting date.",
                                    "data_type": "DateTime",
                                    "xpath": "./Identifications/TaxId/DateOfExpiration"
                                },
                                "IssuanceLocation": {
                                    "description": "The location where the ID was issued.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 32,
                                    "xpath": "./Identifications/TaxId/IssuanceLocation"
                                },
                                "IssuedBy": {
                                    "description": "The name or organization which issued the document.",
                                    "mandatory": False,
                                    "data_type": "String",
                                    "length": 128,
                                    "xpath": "./Identifications/TaxId/IssuedBy"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Helper functions for validation
def validate_national_id(id_number):
    """Validate National ID format"""
    pattern = VALIDATION_RULES["document_rules"]["national_id"]["pattern"]
    return bool(re.match(pattern, id_number))

def validate_phone_number(phone_number):
    """Validate phone number format"""
    pattern = VALIDATION_RULES["contact_rules"]["phone"]["cellular"]["pattern"]
    return bool(re.match(pattern, phone_number))

def get_currency_description(code):
    """Get currency description from code"""
    for curr in VALIDATION_RULES["currency_codes"]["by_id"].values():
        if curr["code"] == code:
            return curr["description"]
    return None

# Define validation dictionaries for BOT command structure
validation_dict = {
    'lookup_tables': {
        'InstallmentType': {
            'name': 'InstalmentType',
            'values': {'Fixed': 'Fixed'}
        },
        'CollateralType': {
            'name': 'CollateralType',
            'values': {'Other': 'Other'}
        },
        'RoleOfClient': {
            'name': 'RoleOfClient',
            'values': {'MainDebtor': 'MainDebtor'}
        },
        'CountryCode': {
            'name': 'CountryCode',
            'values': {'TZ': 'TZ'}
        },
        'District': {
            'name': 'District',
            'values': {'Moshi': 'Moshi'}
        },
        'Region': {
            'name': 'Region',
            'values': {'Arusha': 'Arusha'}
        },
        'LegalForm': {
            'name': 'LegalForm',
            'values': {'GovernmentalInstitution': 'GovernmentalInstitution'}
        },
        'Currency': {
            'name': 'Currency',
            'values': {'TZS': 'TZS'}
        },
        'NegativeStatusOfLoan': {
            'name': 'NegativeStatusOfLoan',
            'values': {'NoNegativeStatus': 'NoNegativeStatus'}
        },
        'PhaseOfLoan': {
            'name': 'PhaseOfLoan',
            'values': {'Existing': 'Existing'}
        },
        'Bool': {
            'name': 'Bool',
            'values': {'False': 'False', 'True': 'True'}
        }
    },
    'economic_sectors': {
        'OtherServices': {'code': 'S', 'description': 'Other Services'}
    }
}

# Simple reverse lookup
validation_dict_by_code = {
    'economic_sectors': {
        'S': 'OtherServices',
        'A': 'Agriculture',
        'M': 'Manufacturing'
    },
    'districts': {
        'MSH': 'Moshi'
    },
    'regions': {
        'ARS': 'Arusha'
    }
}

# Update validate_code function to handle lookup tables
def validate_code(category, code=None, code_id=None):
    """
    Validate a code or code_id against the dictionary.
    
    Args:
        category (str): Category name (economic_sectors, districts, regions, or any lookup table code)
        code (str, optional): The code value to validate
        code_id (int/str, optional): The code ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if category.startswith('D') and category in validation_dict["lookup_tables"]:
        if code is not None:
            return any(item["value"] == code for item in validation_dict["lookup_tables"][category]["values"].values())
        if code_id is not None:
            return code_id in validation_dict["lookup_tables"][category]["values"]
        return False
        
    if category not in validation_dict:
        return False
        
    if code is not None:
        return code in validation_dict_by_code[category]
    
    if code_id is not None:
        return code_id in validation_dict[category]
        
    return False

# Update XML validation to handle lookup tables
def validate_xml_element(element, category, attribute_name):
    """
    Validate an XML element against the dictionary.
    
    Args:
        element: The XML element to validate
        category (str): Category name including lookup table codes
        attribute_name (str): The attribute containing the code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if attribute_name not in element.attrib:
        return False
        
    code = element.attrib[attribute_name]
    return validate_code(category, code=code)

# Example usage:
"""
# Validate individual classification
valid = validate_code("D01", code="Individual")  # True

# Validate marital status
valid = validate_code("D17", code="Married")  # True

# Validate education level
valid = validate_code("D20", code="University")  # True
"""

# Add XML namespace configuration
XML_NAMESPACE = {
    'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'
}

def validate_xml_file(xml_content):
    """
    Validate XML content against BOT rules using exact error checking
    """
    try:
        tree = ET.fromstring(xml_content)
        validation_errors = []
        ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}

        # Process each Command element
        for command in tree.findall('.//ns:Command', ns):
            identifier = command.get('identifier', '')
            company = command.find('.//ns:Company', ns)
            
            if company is not None:
                # CompanyData validation
                company_data = company.find('.//ns:CompanyData', ns)
                if company_data is not None:
                    # Validate Trade Name
                    trade_name = company_data.findtext('ns:TradeName', '', ns)
                    if not trade_name or not trade_name.strip():
                        validation_errors.append(f"Missing Trade Name in Command {identifier}")

                    # Validate Registration Number
                    reg_num = company_data.findtext('ns:RegistrationNumber', '', ns)
                    if not reg_num or not reg_num.strip():
                        validation_errors.append(f"Missing Registration Number in Command {identifier}")

                    # Validate Economic Sector
                    sector = company_data.find('ns:EconomicSector', ns)
                    if sector is None or not sector.get('code'):
                        validation_errors.append(f"Missing Economic Sector in Command {identifier}")
                    elif sector.get('code') not in validation_dict_by_code.get('economic_sectors', {}):
                        validation_errors.append(f"Invalid Economic Sector code in Command {identifier}")

                # ContactsCompany validation
                contacts = company.find('.//ns:ContactsCompany', ns)
                if contacts is not None:
                    phone = contacts.findtext('ns:CellularPhone', '', ns)
                    if not phone or not phone.strip():
                        validation_errors.append(f"Missing Phone Number in Command {identifier}")

        # Update validation results
        return {
            'is_valid': len(validation_errors) == 0,
            'errors': validation_errors,
            'error_count': len(validation_errors),
            'message': "XML file is valid and ready for BOT submission" if len(validation_errors) == 0 
                      else f"Found {len(validation_errors)} validation errors that must be corrected before BOT submission"
        }

    except ET.ParseError as e:
        return {
            'is_valid': False,
            'errors': [f"XML Parse Error: {str(e)}"],
            'error_count': 1,
            'message': f"Invalid XML structure: {str(e)}"
        }
    except Exception as e:
        return {
            'is_valid': False,
            'errors': [f"Validation Error: {str(e)}"],
            'error_count': 1,
            'message': f"Error during validation: {str(e)}"
        }

def get_xml_value(element, xpath, namespaces=XML_NAMESPACE):
    """Helper function to safely get XML element value"""
    elem = element.find(xpath, namespaces)
    return elem.text.strip() if elem is not None and elem.text else None

BOT_REQUIRED_FIELDS = {
    'CompanyData': [
        'EstablishmentDate',
        'NegativeStatusOfClient',
        'NumberOfEmployees',
        'RegistrationCountry',
        'TaxIdentificationNumber',
        'LegalForm',
        'RegistrationNumber',
        'TradeName',
        'EconomicSector'
    ],
    'Instalment': [
        'InstalmentCount',
        'InstalmentType',
        'OutstandingAmount',
        'PeriodicityOfPayments',
        'TypeOfInstalmentLoan'
    ]
}

validation_dict = {
    'command_structure': {
        'StorInstalment': {
            'required_sections': {
                'Instalment': {
                    'required_fields': {
                        'InstalmentCount': {'type': 'int', 'required': True},
                        'InstalmentType': {'type': 'lookup', 'value': 'InstalmentType.Fixed'},
                        'OutstandingAmount': {'type': 'decimal', 'required': True},
                        'OutstandingInstalmentCount': {'type': 'int', 'required': True},
                        'OverdueInstalmentCount': {'type': 'int', 'required': True},
                        'PeriodicityOfPayments': {'type': 'lookup', 'value': 'PeriodicityOfPayments.AnnualInstalments360Days'},
                        'StandardInstalmentAmount': {'type': 'decimal', 'required': True},
                        'TypeOfInstalmentLoan': {'type': 'lookup', 'value': 'TypeOfInstalmentLoan.BusinessLoan'},
                        'CurrencyOfLoan': {'type': 'lookup', 'value': 'Currency.TZS'},
                        'EconomicSector': {'type': 'lookup', 'value': 'EconomicSector.OtherServices'},
                        'NegativeStatusOfLoan': {'type': 'lookup', 'value': 'NegativeStatusOfLoan.NoNegativeStatus'},
                        'PastDueAmount': {'type': 'decimal', 'required': True},
                        'PhaseOfLoan': {'type': 'lookup', 'value': 'PhaseOfLoan.Existing'},
                        'RescheduledLoan': {'type': 'lookup', 'value': 'Bool.False'},
                        'TotalLoanAmount': {'type': 'decimal', 'required': True}
                    },
                    'nested_sections': {
                        'ConnectedSubject': {
                            'Company': {
                                'required_fields': {
                                    'CustomerCode': {'type': 'string', 'required': True}
                                },
                                'nested_sections': {
                                    'CompanyData': {
                                        'required_fields': {
                                            'EstablishmentDate': {'type': 'datetime', 'required': True},
                                            'LegalForm': {'type': 'lookup', 'value': 'LegalForm.GovernmentalInstitution'},
                                            'RegistrationNumber': {'type': 'string', 'required': True},
                                            'TradeName': {'type': 'string', 'required': True}
                                        }
                                    },
                                    'AddressesCompany': {
                                        'Registration': {
                                            'required_fields': {
                                                'Country': {'type': 'lookup', 'value': 'CountryCode.TZ'},
                                                'District': {'type': 'lookup', 'value': 'District.Moshi'},
                                                'Region': {'type': 'lookup', 'value': 'Region.Arusha'}
                                            }
                                        }
                                    },
                                    'ContactsCompany': {
                                        'required_fields': {
                                            'CellularPhone': {'type': 'string', 'required': True}
                                        }
                                    }
                                }
                            }
                        },
                        'ContractDates': {
                            'required_fields': {
                                'ExpectedEnd': {'type': 'datetime', 'required': True},
                                'RealEnd': {'type': 'datetime', 'required': True},
                                'Start': {'type': 'datetime', 'required': True}
                            }
                        }
                    }
                },
                'StorHeader': {
                    'required_fields': {
                        'Source': {'type': 'string', 'value': 'CBT'},
                        'StoreTo': {'type': 'datetime', 'required': True},
                        'Identifier': {'type': 'string', 'required': True}
                    }
                }
            }
        }
    }
}

# Lookup tables for validation
validation_dict_by_code = {
    'economic_sectors': {
        'S': 'OtherServices',
        'A': 'Agriculture',
        'M': 'Manufacturing'
    },
    'districts': {
        'MSH': 'Moshi'
    },
    'regions': {
        'ARS': 'Arusha'
    }
}