import utils
from tabulate import tabulate
from tqdm import tqdm
from simple_term_menu import TerminalMenu

def main():
    main_menu_title = "  PYTHON DRIVE CONNECT\n  Premi Q o Esc per uscire \n"
    main_menu_items = [
        "[0] Ricarica dati",
        "[1] Visualizza i Drive condivisi",
        "[2] Visualizza i Drive condivisi con un utente/gruppo",
        "[3] Visualizza i permessi di un Drive condiviso",
        "[4] Aggiungi un permesso a un Drive condiviso",
        "[5] Rimuovi un permesso a un Drive condiviso",
        "[6] Aggiorna i permessi di più Drive condivisi",
        "[7] Visualizza gli utenti del dominio",
        "[8] Disconnettiti",
        "[9] Esci",
    ]
    main_menu_cursor = "> "
    main_menu_cursor_style = ("fg_cyan", "bold")
    main_menu_style = ("bg_cyan", "fg_black")
    main_menu_exit = False
    
    main_menu = TerminalMenu(
        menu_entries=main_menu_items,
        title=main_menu_title,
        menu_cursor=main_menu_cursor,
        menu_cursor_style=main_menu_cursor_style,
        menu_highlight_style=main_menu_style,
        cycle_cursor=True,
        clear_screen=True,
    )
        
    try:
        drive_service, directory_service = utils.authenticate_services()
        
        while not main_menu_exit:
            main_sel = main_menu.show()
            
            # Ricaricare i dati
            if main_sel == 0:
                utils.update_data(drive_service)
                input("\n\nPremi invio per continuare... ")
                
            # Visualizzare i drive condivisi
            elif main_sel == 1:
                drives = utils.get_all_drives(drive_service, True)
                drives_formatted = []
                print(f"Drive trovati: {len(drives)}")
                show_all = input("Vuoi visualizzare o esportare tutti i drive? [v/e] ")
                if show_all == 'v':
                    print()
                    for drive in drives:
                        id = drive.get('id', 'N/A')
                        name = drive.get('name', 'N/A')
                        drives_formatted.append([id, name])
                    print(tabulate(drives_formatted, headers=['Id', 'Nome'], tablefmt="simple_grid"))
                    input("\n\nPremi invio per continuare... ")
                elif show_all == 'e':
                    file_name = "shared_drives.csv"
                    with open(file_name, 'w') as file:
                        file.write("Id,Nome\n")
                        for drive in drives:
                            print(drive)
                            id = drive.get('id', 'N/A')
                            name = drive.get('name', 'N/A')
                            file.write(f"{id},{name}\n")
                    print(f"Drive esportati in {file_name}")
                    input("\n\nPremi invio per continuare... ")
                    
            # Visualizzare i drive condivisi con un utente/gruppo
            elif main_sel == 2:
                email = input("Inserisci l'email dell'utente/gruppo: ")
                user_drives = utils.get_drives_shared_with_member(drive_service, email)
                user_drives_formatted = []
                print(f"Drive trovati: {len(user_drives)}")
                show_all = input("Vuoi visualizzare tutti i drive? [y/n] ")
                if show_all == 'y':
                    print()
                    for drive in user_drives:
                        id = drive.get('id', 'N/A')
                        name = drive.get('name', 'N/A')
                        user_drives_formatted.append([id, name])
                    print(tabulate(user_drives_formatted, headers=['Id', 'Nome'], tablefmt="simple_grid"))
                    input("\n\nPremi invio per continuare... ")
                    
            # Visualizzare i permessi di un drive condiviso
            elif main_sel == 3:
                drive_id = input("Inserisci l'ID del drive condiviso: ")
                permissions = utils.get_drive_permissions(drive_service, drive_id)
                permissions_formatted = []
                print()
                for permission in permissions:
                    id = permission.get('id', 'N/A')
                    email = permission.get('emailAddress', 'N/A')
                    type = permission.get('type', 'N/A')
                    role = permission.get('role', 'N/A')
                    permissions_formatted.append([id, email, type, role])
                print(tabulate(permissions_formatted, headers=['Id', 'Email', 'Tipo', 'Ruolo'], tablefmt="simple_grid"))
                input("\n\nPremi invio per continuare... ")
            
            # Aggiungere un permesso a un drive condiviso
            elif main_sel == 4:
                drive_id = input("Inserisci l'ID del drive condiviso: ")
                email = input("Inserisci l'email dell'utente/gruppo: ")
                type = input("Inserisci il tipo di permesso: [user/group] ")
                role = input("Inserisci il ruolo: [organizer/fileOrganizer/writer/commenter/reader] ")
                while role not in ["organizer", "fileOrganizer", "writer", "commenter", "reader"]:
                    print("Ruolo non valido")
                    role = input("Inserisci il ruolo: [organizer/fileOrganizer/writer/commenter/reader] ")
                    continue
                print()
                if utils.create_drive_permission(drive_service, drive_id, email, type, role):
                    print(f"Permesso aggiunto con successo")
                else:
                    print(f"Errore durante l'aggiunta del permesso")
                input("\n\nPremi invio per continuare... ")
            
            # Rimuovere un permesso a un drive condiviso
            elif main_sel == 5:
                drive_id = input("Inserisci l'ID del drive condiviso: ")
                permission_id = input("Inserisci l'ID del permesso da rimuovere: ")
                print()
                if(utils.delete_drive_permission(drive_service, drive_id, permission_id)):
                    print(f"Permesso rimosso con successo")
                else:
                    print(f"Errore durante la rimozione del permesso")
                input("\n\nPremi invio per continuare... ")
            
            # Aggiornare i permessi di più drive condivisi
            elif main_sel == 6:
                new_permissions = []
                num_permissions = input("Quanti permessi vuoi aggiungere? ")
                utils.clear()
                for i in range(int(num_permissions)):
                    print(f"{i+1}^ permesso\n")
                    email = input("Inserisci l'email dell'utente/gruppo: ")
                    type = input("Inserisci il tipo di permesso: [user/group] ")
                    role = input("Inserisci il ruolo: [organizer/fileOrganizer/writer/commenter/reader] ")
                    while role not in ["organizer", "fileOrganizer", "writer", "commenter", "reader"]:
                        print("Ruolo non valido")
                        role = input("Inserisci il ruolo: [organizer/fileOrganizer/writer/commenter/reader] ")
                        continue
                    new_permissions.append({"email": email, "type": type, "role": role})
                    utils.clear()
                
                drives_affected = input("Quanti drive vuoi aggiornare? [1/2/.../all] ")
                print()
                drives = []
                if drives_affected == "all":
                    drives_exclusion = input("Vuoi escludere determinati drive? [y/n] ")
                    print()
                    if drives_exclusion == 'y':
                        excluded_drives = []
                        while True:
                            excluded_drive = input("Inserisci l'ID di drive da escludere (o premi invio per terminare): ")
                            if not excluded_drive:
                                break
                            excluded_drives.append(excluded_drive)
                        drives = utils.get_all_drives(drive_service, True)
                        drives = [drive for drive in drives if drive['id'] not in excluded_drives]
                    else:
                        drives = utils.get_all_drives(drive_service, True)
                else:
                    for i in range(int(drives_affected)):
                        drive_id = input(f"Inserisci l'ID del {i+1}^ drive: ")
                        drives.append({"id": drive_id})
                print()
                print(drives)
                if input(f"Sei sicuro di voler aggiornare i permessi di {len(drives)} drive? [y/n] ") == 'y':
                    for drive in tqdm(drives):
                        drive_id = drive.get('id', 'N/A')
                        permissions = utils.get_drive_permissions(drive_service, drive_id)
                        for permission in permissions:
                            utils.delete_drive_permission(drive_service, drive_id, permission.get('id'))
                        for permission in new_permissions:
                            utils.create_drive_permission(drive_service, drive_id, permission.get('email'), permission.get('type'), permission.get('role'))
                    input("\n\nPremi invio per continuare... ")
            
            # Visualizzare gli utenti del dominio
            elif main_sel == 7:
                users = utils.get_all_users(directory_service)
                users_formatted = []
                print(f"Utenti trovati: {len(users)}")
                show_all = input("Vuoi visualizzare o esportare tutti gli utenti? [v/e] ")
                if show_all == 'v':
                    print()
                    for user in users:
                        id = user.get('id', 'N/A')
                        email = user.get('primaryEmail', 'N/A')
                        name = user.get('name', {}).get('fullName', 'N/A')
                        is_admin = 'Sì' if user.get('isAdmin', False) else 'No'
                        status = 'ATTIVO' if not user.get('suspended', False) else 'SOSPESO'
                        users_formatted.append([id, email, name, is_admin, status])
                    print(tabulate(users_formatted, headers=['Id', 'Email', 'Nome', 'Admin', 'Stato'], tablefmt="simple_grid"))
                    input("\n\nPremi invio per continuare... ")
                elif show_all == 'e':
                    file_name = "users.csv"
                    with open(file_name, 'w') as file:
                        file.write("Id,Email,Nome,Admin,Stato\n")
                        for user in users:
                            id = user.get('id', 'N/A')
                            email = user.get('primaryEmail', 'N/A')
                            name = user.get('name', {}).get('fullName', 'N/A')
                            is_admin = 'SI' if user.get('isAdmin', False) else 'NO'
                            status = 'ATTIVO' if not user.get('suspended', False) else 'SOSPESO'
                            file.write(f"{id},{email},{name},{is_admin},{status}\n")
                    print(f"Utenti esportati in {file_name}")
                    input("\n\nPremi invio per continuare... ")
                        
            elif main_sel == 8:
                utils.delete_token()
                utils.delete_data()
                main_menu_exit = True
                
            elif main_sel == 9 or main_sel == None:
                main_menu_exit = True
            
      
    except utils.HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()