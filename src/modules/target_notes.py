"""target_notes.py"""
from sqlalchemy.orm.query import Query
from typing import List, Literal, LiteralString
from rich.console import Console
from rich.table import Table
from rich.text import Text
from modules.database import Database
from models import TargetModel, TargetNoteModel
from prompt_toolkit import PromptSession
from urllib.parse import urlparse, parse_qs

class TargetNotes:
    """Target Notes."""
    def __init__(self, app_obj, args):
        self.app_obj = app_obj
        self.args = args

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return

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

    def _add_note(self) -> None:
        """Add a note about the target.

        Returns:
            None
        """
        selected_target: TargetModel = self.app_obj._get_selected_target()
        if selected_target is None:
            print("\nPlease select a target before using the 'scope' option.\n")
            return

        selected_target = self.app_obj.selected_target_obj

        target_path = input("Input the target path for this note (or press enter to leave blank):\n")
        if target_path == '':
            target_path = None
        print("")

        print("Input/Paste content, then press CTRL-D or CTRL-Z (on Windows OS) to save it.")
        lines = []
        while True:
            try:
                line: str = input()
            except EOFError:
                break
            lines.append(line)

        target_note: LiteralString = '\n'.join(lines)

        print("\n************************************************\n")
        print(target_note)
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
        
        db = TargetDatabase()
        db_session: Session = db.session_local()

        try:
            new_target_scope = TargetNoteModel(
                target_id = selected_target.id,
                full_note = str(target_note),
                path = target_path
            )
            result: Literal[0] | Literal[1] = db._add_targetnote(db_session, new_target_scope) # pylint: disable=W0212
            if result == 0:
                print("Target note added to the database.\n")
            elif result == 1:
                print("Target note already exists.\n")
            else:
                print("There was an error trying to add the target note scope.\n")
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
                records: List[TargetNoteModel] = db.query(TargetNoteModel).filter(TargetNoteModel.active == True)\
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
                        full_note=record.full_note
                    )
                    targetnotes.append(targetnote_record)

                target_summaries = []
                for note in targetnotes:
                    target_summaries.append({'summary':note.summary or '','path':note.path or ''})

                table = Table(show_lines=True)
                table.add_column('#')
                table.add_column('summary', width=80)
                table.add_column('path')

                counter = 0
                for target in targetnotes:
                    if target.path is not None:
                        if len(target.path) > 80:
                            segments = [target.path[i:i+75] for i in range(0, len(target.path), 75)]
                            text_segments = [Text(segment) for segment in segments]
                            wrapped_path = Text("\n".join(str(segment) for segment in text_segments))
                            table.add_row(str(counter), target.summary, wrapped_path)
                        else:
                            table.add_row(str(counter), Text(target.summary), Text(target.path))
                    else:
                        table.add_row(str(counter), target.summary, target.path)
                    counter += 1
                
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

    def _select_note(self, selected_target: TargetModel, selected_no, targetnotes: TargetNoteModel):
        """View Note"""
        self.app_obj._clear()
        print(f"TARGET NOTE\n")

        print(f"Target: {selected_target.name}\n")
        print(f"Note Id: {targetnotes[selected_no].id}")
        print(f"Note Created: {targetnotes[selected_no].created_timestamp}")
        print("")

        if targetnotes[selected_no].url is not None:
            print(f"URL: {targetnotes[selected_no].url}")
            parsed_url = urlparse(targetnotes[selected_no].url)
            query_params = parse_qs(parsed_url.query)
            if len(query_params) > 0:
                print("\nURL Params:")
                for param, value in query_params.items():
                    print(f"{param}: {value}")

        if targetnotes[selected_no].path is not None:
            print(f"\nPath: {targetnotes[selected_no].path}")
            print("")

        print("************************************************\n")
        print(targetnotes[selected_no].full_note)
        print("\n************************************************\n")

        print("Do you want to delete this note (`yes`/`no`) ?")
        prompt_session = PromptSession()
        prompt_user = True
        while prompt_user:
            text = prompt_session.prompt(' > ')
            if '' == text or 'no' == text:
                prompt_user = False
            elif 'yes' == text:
                prompt_user = False
                confirm = input("Are you sure you want to delete (`yes`/`no`) ?")
                if 'yes' == confirm:
                    db = TargetDatabase()
                    db_session: Session = db.session_local()
                    db._delete_targetnote(db_session,targetnotes[selected_no]['id']) # pylint: disable=W0212
                    print("Note deleted!")
                else:
                    return
