"""target_notes.py"""
import re
from sqlalchemy.orm.query import Query
from typing import List, Literal, LiteralString
from rich.console import Console
from rich.table import Table
from rich.text import Text
from modules.database import Database
from models import ChecklistModel, TargetModel, TargetNoteModel
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.shortcuts import input_dialog
from urllib.parse import urlparse, parse_qs

class TargetNotes:
    """Target Notes."""
    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args
        self.prompt_user = False

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return

        if len(self.args) == 3:
            checklist_item_id = None
            match = re.search(r"\[\[item_id=(.*?)\]\]", self.args[2])
            if match:
                checklist_item_id = match.group(1)
                self._add_note(checklist_item_id)
            else:
                return
        else:
            try:
                class_name = self.args[1]
                function_name = self.args[0]
                args = []
                match class_name:
                    case 'note':
                        function_name = f"_{function_name}_note"
                    case 'notes':
                        function_name = f"_{function_name}_notes"
                    case _:
                        return

                func = getattr(self, function_name)
                if callable(func):
                    func(*args)
                else:
                    print('Else: Function is not callable:%s',function_name)
            except AttributeError:
                return
            except Exception as exc:
                print(exc)

    def _add_note(self, checklist_item_id=None) -> None:
        """Add a note about the target.

        Returns:
            None
        """
        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target is None:
            print("\nPlease select a target before using the 'note' option.\n")
            return

        target_path = input("Input the target path for this note (or press enter to leave blank):\n")
        if target_path == '':
            target_path = None
        print("")

        print("Input/Paste content, then press CTRL-D or CTRL-Z (on Windows OS) to save it.")

        session = PromptSession()
        target_note = session.prompt("NOTE DETAILS:\n\n", multiline=True)
        
        print("\n************************************************\n")
        print_formatted_text(target_note)
        print("\n************************************************\n")

        save_to_database = False
        confirm: str = input("Is this correct? (`y` or enter == yes; `n` == no)")
        if '' == confirm or 'y' == confirm.lower() or 'yes' == confirm.lower().strip():
            save_to_database = True

        if 'n' == confirm.lower().strip() or 'N' == confirm.lower().strip():
            print("Canceled.")
            return

        if save_to_database == False:
            print("Canceled.")
            return

        with Database._get_db() as db:
            try:
                new_target_scope = TargetNoteModel(
                    target_id = selected_target.id,
                    full_note = str(target_note),
                    checklist_item_id=checklist_item_id,
                    path = target_path
                )
                db.add(new_target_scope)
                db.commit()
                db.refresh(new_target_scope)
            except Exception as database_exception: # pylint: disable=W0718
                print(database_exception)

    def _view_notes(self) -> None:
        """List all active notes.

        Returns:
            None
        """
        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target is None:
            print("\nPlease select a target before using the 'notes' option.\n")
            return

        self.app_obj._clear()
        print(f"TARGET NOTES\n")
        print(f"Target: {selected_target.name}")

        try:
            targetnotes: List[TargetNoteModel] = []
            with Database._get_db() as db:
                records: List[TargetNoteModel] = db.query(TargetNoteModel)\
                    .filter(TargetNoteModel.active == True)\
                    .filter_by(target_id=selected_target.id)\
                    .order_by(TargetNoteModel.created_timestamp).all()

                for record in records:
                    tmp_full_note = record.full_note
                    if len(tmp_full_note) > 400:
                        tmp_full_note = tmp_full_note[:400] + " ..."

                    targetnote_record = TargetNoteModel(
                        id=record.id,
                        target_id=record.target_id,
                        created_timestamp=record.created_timestamp,
                        modified_timestamp=record.modified_timestamp,
                        fqdn=record.fqdn,
                        path=record.path,
                        url=record.path,
                        page=record.page,
                        summary=tmp_full_note,
                        full_note=record.full_note,
                        checklist_item_id=record.checklist_item_id
                    )
                    targetnotes.append(targetnote_record)

                target_summaries = []
                has_checklist_item = False
                for note in targetnotes:
                    if note.checklist_item_id is not None:
                        has_checklist_item = True
                    if has_checklist_item:
                        target_summaries.append({'checklist_item_id':note.checklist_item_id or '','summary':note.summary or '','path':note.path or ''})
                    else:
                        target_summaries.append({'summary':note.summary or '','path':note.path or ''})

                if has_checklist_item:
                    table = Table(show_lines=True)
                    table.add_column('#', width=15)
                    table.add_column('checklist_item', width=20)
                    table.add_column('summary', width=70)
                    table.add_column('path', width=80)

                    counter = 0
                    for target in targetnotes:
                        table.add_row(str(counter), Text(target.checklist_item_id or ''), Text(target.summary or '', overflow="clip", no_wrap=False), Text(target.path or '', overflow="clip", no_wrap=False))
                        counter += 1
                else:
                    print("no checklist")
                    table = Table(show_lines=True)
                    table.add_column('#', width=10)
                    table.add_column('summary', width=70)
                    table.add_column('path', width=80)

                    counter = 0
                    for target in targetnotes:
                        table.add_row(str(counter), Text(target.summary or '', overflow="clip", no_wrap=False), Text(target.path or '', overflow="clip", no_wrap=False))
                        counter += 1
                
                print("now print the table...")
                console = Console()
                console.print(table)

                selected: str = input("Select a note by # (leave blank to cancel): ")
                if '' == selected:
                    return
                try:
                    selected_no = int(selected)
                    self._select_note(selected_target, selected_no, targetnotes)
                except ValueError:
                    print("ERROR: Invalid input. Input a valid number.")
        except Exception as database_exception: # pylint: disable=W0718
            print(database_exception)

    def _get_checklist_notes(self, selected_target: TargetModel, checklist_record: ChecklistModel):
        targetnotes: List[TargetNoteModel] = []
        if checklist_record.item_id is None:
            try:
                with Database._get_db() as db:
                    records: List[TargetNoteModel] = db.query(TargetNoteModel)\
                        .filter(TargetNoteModel.active == True)\
                        .filter_by(target_id=selected_target.id)\
                        .filter(TargetNoteModel.checklist_item_id.is_not(None))\
                        .order_by(TargetNoteModel.checklist_item_id).all()
                    for record in records:
                        tmp_full_note = record.full_note
                        if len(tmp_full_note) > 400:
                            tmp_full_note = tmp_full_note[:400] + " ..."

                        targetnote_record = TargetNoteModel(
                            id=record.id,
                            target_id=record.target_id,
                            created_timestamp=record.created_timestamp,
                            modified_timestamp=record.modified_timestamp,
                            fqdn=record.fqdn,
                            path=record.path,
                            url=record.path,
                            page=record.page,
                            summary=tmp_full_note,
                            full_note=record.full_note,
                            checklist_item_id=record.checklist_item_id
                        )
                        targetnotes.append(targetnote_record)   

                if targetnotes:
                    table = Table(show_lines=True, title=f"Checklist Notes for {selected_target.name}")
                    table.add_column('#', width=20)
                    table.add_column('checklist_item', width=20)
                    table.add_column('path', width=100)

                    counter = 0
                    for target in targetnotes:
                        table.add_row(str(counter), Text(target.checklist_item_id), Text(target.path, overflow="clip", no_wrap=False))
                        counter += 1

                    console = Console()
                    print()
                    console.print(table)

            except Exception as exc:
                print(exc)
        else:
            try:
                with Database._get_db() as db:
                    records: List[TargetNoteModel] = db.query(TargetNoteModel)\
                        .filter(TargetNoteModel.active == True)\
                        .filter_by(target_id=selected_target.id)\
                        .filter_by(checklist_item_id=checklist_record.item_id)\
                        .order_by(TargetNoteModel.created_timestamp).all()
                    for record in records:
                        tmp_full_note = record.full_note
                        if len(tmp_full_note) > 400:
                            tmp_full_note = tmp_full_note[:400] + " ..."

                        targetnote_record = TargetNoteModel(
                            id=record.id,
                            target_id=record.target_id,
                            created_timestamp=record.created_timestamp,
                            modified_timestamp=record.modified_timestamp,
                            fqdn=record.fqdn,
                            path=record.path,
                            url=record.path,
                            page=record.page,
                            summary=tmp_full_note,
                            full_note=record.full_note,
                            checklist_item_id=record.checklist_item_id
                        )
                        targetnotes.append(targetnote_record)   

                if targetnotes:
                    table = Table(show_lines=True, title=f"Notes for {selected_target.name}")
                    table.add_column('#', width=20)
                    table.add_column('summary', width=50)
                    table.add_column('path', width=100)

                    counter = 0
                    for target in targetnotes:
                        table.add_row(str(counter), Text(target.summary, overflow="clip", no_wrap=False), Text(target.path, overflow="clip", no_wrap=False))
                        counter += 1

                    console = Console()
                    print()
                    console.print(table)

            except Exception as exc:
                print(exc)

    def _select_note(self, selected_target: TargetModel, selected_no, targetnotes: List[TargetNoteModel]):
        """View Note"""
        self.app_obj._clear()
        print(f"TARGET NOTE\n")

        selected_note: TargetNoteModel = targetnotes[selected_no]

        print(f"Target: {selected_target.name}\n")
        print(f"Note Id: {selected_note.id}")
        print(f"Note Created: {selected_note.created_timestamp}")

        if selected_note.checklist_item_id is not None:
            print(f"Checklist Item Id: {selected_note.checklist_item_id}")
        print("")

        if selected_note.url is not None:
            print(f"URL: {selected_note.url}")
            parsed_url = urlparse(selected_note.url)
            query_params = parse_qs(parsed_url.query)
            if len(query_params) > 0:
                print("\nURL Params:")
                for param, value in query_params.items():
                    print(f"{param}: {value}")

        if selected_note.path is not None:
            print(f"\nPath: {selected_note.path}")
            print("")

        print("************************************************\n")
        print(selected_note.full_note)
        print("\n************************************************\n")

        #print("Do you want to delete this note (`yes`/`no`) ?")
        print("What do you want to do next ('edit', 'delete', enter = CANCEL) ?")
        prompt_session = PromptSession()
        prompt_user = True
        while prompt_user:
            text = prompt_session.prompt(' > ')
            if '' == text or 'no' == text:
                prompt_user = False
            elif 'delete' == text:
                prompt_user = False
                confirm = input("Are you sure you want to delete (`yes`/`no`) ?")
                if 'yes' == confirm:
                    with Database._get_db() as db:
                        try:
                            record_to_delete: TargetNoteModel | None = db.query(TargetNoteModel).filter_by(id=selected_note.id).first()
                            if record_to_delete:
                                db.delete(record_to_delete)
                                db.commit()
                                print("Target note deleted successfully.")
                            else:
                                print("Target note not found.")
                        except Exception as exc:
                            print(exc)
                else:
                    return
            elif 'edit' == text:
                updated_data = None
                while True:
                    try:
                        prompt_user = False
                        session = PromptSession()
                        formatted_data = f"[[TITLE:]]\n{selected_note.url}\n[[NOTE:]]\n{selected_note.full_note}"
                        updated_data = session.prompt("Edit the note:\n\n", default=formatted_data, multiline=True)
                        break
                    except KeyboardInterrupt:
                        break
                    except EOFError:
                        break
                    except Exception as exc:
                        print(exc)
                        break

                new_url = None
                new_full_note = None
                if updated_data is not None:
                    lines = updated_data.splitlines()
                    url_start = 0
                    note_start = 0
                    num_lines = 0
                    for i, line in enumerate(lines):
                        if '[[TITLE:]]' == line:
                            url_start = i
                        elif '[[NOTE:]]' == line:
                            note_start = i
                        num_lines = i + 1
                    for i, line in enumerate(lines):
                        if i > url_start and i < note_start:
                            if new_url is None:
                                new_url = line
                            else:
                                new_url = new_url + "\n" + line
                        if i > note_start and i <= len(lines):
                            if new_full_note is None:
                                new_full_note = line
                            else:
                                new_full_note = new_full_note + "\n" + line

                    print()
                    console = Console()
                    console.print("NEW URL:", style="underline")
                    print()
                    print(new_url)
                    print()

                    console.print("NEW NOTE:", style="underline")
                    print()
                    print(new_full_note)
                    print()

                    print("---------------------------------------------")
                    confirm = input("Save this update? \n('y','yes' == SAVE; enter,'n','no' == CANCEL)")
                    if confirm.lower() in ('','n','no'):
                        return
                    
                    with Database._get_db() as db:
                        try:
                            existing_record = db.query(TargetNoteModel).filter_by(id=selected_note.id).first()
                            if existing_record:
                                if new_url is not None and '' != new_url and new_full_note is not None and new_full_note != '':
                                    print("Updating the existing record...")
                                    existing_record.url = new_url
                                    existing_record.full_note = new_full_note
                                    db.commit()
                                    db.refresh(existing_record)
                                elif new_full_note is not None and new_full_note != '':
                                    print("Updating the existing record (note only)...")
                                    existing_record.full_note = new_full_note
                                    db.commit()
                                    db.refresh(existing_record)
                                else:
                                    print("Blank data. Cancel.")
                            else:
                                print("Existing record not found.")
                        except Exception as exc:
                            print(exc)

