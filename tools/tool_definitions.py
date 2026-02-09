"""Tool definitions for the agent."""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Henter batteristatus",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_wifi_info",
            "description": "Henter info om WiFi-tilkobling",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_location",
            "description": "Henter GPS-posisjon",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_info",
            "description": "Henter telephony/device info",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Leser utklippstavlen",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Setter utklippstavlen",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Tekst til utklippstavlen"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_sms",
            "description": "Sender en SMS til et spesifisert nummer. Bruk dette for alle endelige svar til brukeren.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Mottakerens telefonnummer"},
                    "message": {"type": "string", "description": "Meldingstekst"}
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_mms",
            "description": "Sender MMS med vedlegg",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Mottakerens telefonnummer"},
                    "message": {"type": "string", "description": "Meldingstekst"},
                    "file_path": {"type": "string", "description": "Filsti til vedlegg"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_photo",
            "description": "Tar et bilde med telefonens kamera (bakside som standard)",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lister filer i en mappe",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Mappe å liste"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Leser de første linjene i en fil",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Filsti"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_task",
            "description": "Planlegger en oppgave. schedule_type: interval, daily, once. For daily bruk daily_time (HH:MM). For once bruk run_at (ISO8601). actions er en liste med tool_name og tool_args. Bruk {last_result} for å referere til forrige verktøyresultat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Navn på oppgaven"},
                    "interval_minutes": {"type": "integer", "description": "Hvor ofte i minutter"},
                    "schedule_type": {"type": "string", "description": "interval, daily, once"},
                    "daily_time": {"type": "string", "description": "HH:MM for daglige oppgaver"},
                    "run_at": {"type": "string", "description": "ISO8601 tidspunkt for engangsoppgaver"},
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool_name": {"type": "string"},
                                "tool_args": {"type": "object"}
                            },
                            "required": ["tool_name"]
                        }
                    }
                },
                "required": ["name", "actions"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Lister planlagte oppgaver",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_task",
            "description": "Deaktiverer en planlagt oppgave",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID på oppgaven"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_memory",
            "description": "Lagrer et minne i user_profile.json",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {"type": "string", "description": "Hva som skal lagres"}
                },
                "required": ["note"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_or_update_contact",
            "description": "Legger til eller oppdaterer en kontakt. Bruk dette når du lærer om nye personer eller får mer kontekst om eksisterende kontakter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Telefonnummer"},
                    "name": {"type": "string", "description": "Navn på personen"},
                    "relationship": {"type": "string", "description": "Relasjon til eieren (f.eks. 'sønn', 'sjef', 'venn')"},
                    "tone_preference": {"type": "string", "description": "Foretrukket tone (formal, normal, casual)"},
                    "context": {"type": "string", "description": "Ekstra kontekst om personen"}
                },
                "required": ["number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_short_term_memory",
            "description": "Oppdaterer korttidsminne med nåværende kontekst, brukerens aktivitet, planer osv. Bruk dette for å huske viktig kontekst fra samtalen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {"type": "string", "description": "Generell kontekst (f.eks. 'brukeren er på jobb')"},
                    "date": {"type": "string", "description": "Dato (dagens dato hvis relevant)"},
                    "location": {"type": "string", "description": "Brukerens plassering"},
                    "activity": {"type": "string", "description": "Hva brukeren gjør"},
                    "plan": {"type": "string", "description": "Noe brukeren planlegger å gjøre senere"}
                }
            }
        }
    }
]
