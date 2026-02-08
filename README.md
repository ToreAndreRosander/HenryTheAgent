# HenryTheAgent
Møt Henry! En liten AI agent som eksisterer som en python applikasjon, kjørende i Termux på en Android telefon (last ned via f-droid, ikke google play).

Henry mottar kommandoer og beskjeder via SMS og svarer med SMS.

Under utvikling og test er det brukt en lokal Qwen 2.5 modell (fungerer OK helt ned til 14B Q4)

## Installering

1. Installer Termux og Termux:API fra f-droid.

2. ```pkg install termux-api python```

3. ```pip isntall requests```

4. ```termux-setup-storage```

5. Kontroller SMS tilgang med ```termux-sms-list```

6. Last ned HenryTheAgent og kjør som en vanlig python applikasjon ```python android_agent.py```

