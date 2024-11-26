import os
import os.path
import json
from tqdm import tqdm
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Se si modificano gli scopes, eliminare il file token.json
SCOPES = [
  "https://www.googleapis.com/auth/drive",
  'https://www.googleapis.com/auth/admin.directory.user.readonly'
]
# Percorso al file delle credenziali
CREDENTIALS_FILE = "credentials.json"


def clear():
    """
    Pulisce il terminale
    """
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)


def authenticate_services():
    """
    Autentica i servizi Drive API e Directory API
    """
    creds = None
    # Il file token.json memorizza i token di accesso e di aggiornamento dell'utente
    # e viene creato automaticamente quando il flusso di autorizzazione viene completato per la prima volta.
    if os.path.exists("token.json"):
      creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # Se non sono disponibili credenziali (valide), consentire all'utente di effettuare l'accesso
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
      # Salva le credenziali per la prossima esecuzione
      with open("token.json", "w") as token:
        token.write(creds.to_json())
    
    drive_service = build("drive", "v3", credentials=creds)
    directory_service = build('admin', 'directory_v1', credentials=creds)
    
    return drive_service, directory_service


def delete_token():
    """
    Elimina il file token.json
    """
    if os.path.exists("token.json"):
        os.remove("token.json")
        print("Token eliminato")
    else:
        print("Token non trovato")
        

def update_data(drive_service):
    """
    Aggiorna i file JSON
    """
    drives = []
    permissions = {}
    try:
        if os.path.exists("shared_drives.json"):
            drives = get_all_drives(drive_service, True)
            os.remove("shared_drives.json")
        get_all_drives(drive_service, True)
        print()
        if os.path.exists("permissions.json"):
            permissions = get_all_drives_permissions(drive_service)
            os.remove("permissions.json")
        get_all_drives_permissions(drive_service)
    except KeyboardInterrupt:
        print("\nInterruzione rilevata. Ripristino dati...")
        save_to_file("shared_drives.json", drives)
        save_to_file("permissions.json", permissions)
        
        
def delete_data():
    """
    Elimina i file JSON
    """
    if os.path.exists("shared_drives.json"):
        os.remove("shared_drives.json")
        print("shared_drives.json eliminato")
    if os.path.exists("permissions.json"):
        os.remove("permissions.json")
        print("permissions.json eliminato")
        

def save_to_file(filename, data):
    """
    Salva dati in un file JSON
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"File {filename} salvato con successo")


def load_from_file(filename):
    """
    Carica dati da un file JSON, se esiste
    """
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            print(f"Caricamento {filename}...")
            return json.load(f)
    return None

  
def get_all_drives(drive_service, useDomainAdminAccess=False):
    """
    Ottenere l'elenco di tutti i drive condivisi
    """
    existing_shared_drives = load_from_file("shared_drives.json")
    if existing_shared_drives:
        return existing_shared_drives
    all_shared_drives = []
    
    print(f"Recupero drive condivisi...")
    request = drive_service.drives().list(
      useDomainAdminAccess=useDomainAdminAccess,
      pageSize=100
    )
    while request is not None:
        response = request.execute()
        all_shared_drives.extend(response.get('drives', []))
        request = drive_service.drives().list_next(previous_request=request, previous_response=response)
        
    save_to_file("shared_drives.json", all_shared_drives)
    return all_shared_drives
      
      
def get_drive_permissions(drive_service, drive_id):
    """
    Ottenere i permessi di un drive condiviso
    """
    permissions = []
    try:
        request = drive_service.permissions().list(
            fileId=drive_id,
            supportsTeamDrives=True,
            useDomainAdminAccess=True,
            fields="permissions(id,emailAddress,type,kind,role),nextPageToken"
        )
        while request is not None:
            response = request.execute()
            permissions.extend(response.get('permissions', []))
            request = drive_service.permissions().list_next(previous_request=request, previous_response=response)
    except Exception as e:
        print(f"Errore durante il recupero dei permessi per il drive {drive_id}: {e}")
    return permissions
  

def get_all_drives_permissions(drive_service):
    """
    Ottenere i permessi di tutti i drive condivisi
    """
    existing_permissions = load_from_file("permissions.json")
    if existing_permissions:
        return existing_permissions
    all_permissions = {}
    shared_drives = get_all_drives(drive_service, True)
    
    print(f"Recupero permessi...")
    for drive in tqdm(shared_drives):
        permissions = get_drive_permissions(drive_service, drive['id'])
        all_permissions[drive['id']] = {
            "name": drive['name'],
            "permissions": permissions
        }
        
    save_to_file("permissions.json", all_permissions)
    return all_permissions
      

def create_drive_permission(drive_service, drive_id, email, type, role):
    """
    Aggiungere un nuovo permesso a un drive condiviso
    """
    permission_body = {
        "type": type,   # 'user', 'group', o 'domain'
        "role": role,   # 'owner', 'organizer', 'fileOrganizer', 'writer', 'commenter', 'reader
    }

    # Aggiungere l'email solo per permessi di tipo 'user' o 'group'
    if type in ["user", "group"]:
        permission_body["emailAddress"] = email

    try:
        drive_service.permissions().create(
            fileId=drive_id,
            body=permission_body,
            supportsTeamDrives=True,
            useDomainAdminAccess=True,
            sendNotificationEmail=False,
            fields="id"
        ).execute()
        return True
    except Exception as e:
        return False
  
  
def delete_drive_permission(drive_service, drive_id, permission_id):
    """
    Rimuovere un permesso da un drive condiviso
    """
    try:
        drive_service.permissions().delete(
            fileId=drive_id,
            permissionId=permission_id,
            supportsTeamDrives=True,
            useDomainAdminAccess=True
        ).execute()
        return True
    except Exception as e:
        return False
    
  
def get_all_users(directory_service):
    """
    Ottenere tutti gli utenti del dominio
    """
    users = []
    request = directory_service.users().list(customer='my_customer', maxResults=200)
    while request is not None:
        response = request.execute()
        users.extend(response.get('users', []))
        request = directory_service.users().list_next(previous_request=request, previous_response=response)
    return users


def get_email_from_id(directory_service, user_id):
    """
    Ottenere l'email di un utente con un determinato id
    """
    users = get_all_users(directory_service)
    for user in users:
        if user.get('id') == user_id:
            return user.get('primaryEmail')
    print(f"Utente con userId {user_id} non trovato")
    return None
  

def get_id_from_email(directory_service, email):
    """
    Ottenere l'id di un utente con una determinata email
    """
    users = get_all_users(directory_service)
    for user in users:
        if user.get('primaryEmail') == email:
            return user.get('id')
    print(f"Utente con email {email} non trovato.")
    return None
  
  
def get_drives_shared_with_member(drive_service, user_email):
    """
    Ottenere l'elenco di tutti i drive condivisi con un determinato utente/gruppo
    """
    shared_drives = get_all_drives(drive_service, True)
    permissions = get_all_drives_permissions(drive_service)
    
    user_shared_drives = []
    
    for drive in shared_drives:
        drive_id = drive.get('id')
        for permission in permissions.get(drive_id).get('permissions'):
  
          if permission.get('emailAddress') == user_email:
              user_shared_drives.append(drive)
              break
    
    return user_shared_drives
  
