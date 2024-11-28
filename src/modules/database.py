"""db.py"""
from contextlib import contextmanager
from typing import Any, Generator, List, Literal
from sqlalchemy import Engine, Result, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import pandas as pd
from rich.console import Console
from rich.table import Table
from models import Base, ChecklistModel, ProxyModel
from models.setupdata import SetupData


CONNECTION_STRING_POSTGRES = 'postgresql://w3bt00lkit:w3bt00lkit@localhost:5432/w3bt00lkit'

class Database():
    """Database."""
    def __init__(self, app_obj, args) -> None:
        self.app_obj = app_obj
        self.args = args
        self.engine: Engine = create_engine(CONNECTION_STRING_POSTGRES, connect_args={'options': '-c statement_timeout=5000'})
        self.db_session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def _get_db() -> Generator[Session, Any, None]: # pylint: disable=E0211
        """Get database."""
        engine: Engine = create_engine(CONNECTION_STRING_POSTGRES, connect_args={'options': '-c statement_timeout=5000'})
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = session()
        try:
            yield db
        finally:
            db.close()

    def _handle_input(self, args):
        """Handle Input."""
        self.args = args
        if len(self.args) < 2:
            return

        try:
            class_name = self.args[0]
            if class_name == 'database':
                function_name = self.args[1]
            else:
                function_name = self.args[0]
            args = []
            func = getattr(self, function_name)
            if callable(func):
                func(*args)
            else:
                print('Else: Function is not callable:%s',function_name)
        except AttributeError:
           return
        except Exception as exc:
            print(exc)

    def _add_request(self, request: ProxyModel) -> ProxyModel:
        """Add request to the database.
        
        Args:
            db (Session): The current session to connect to the database.
            request (ProxyModel): The model used with the request.

        Returns:
           request (ProxyModel): The updated model that was used with the request.
        """
        with Database._get_db() as db:
            db.add(request)
            db.commit()
            db.refresh(request)
        return request

    def _add_checklist(self, db: Session, checklist: ChecklistModel) -> Literal[0] | Literal[1]:
        """Add checklist item to the database.
        
        Args:
            db (Session): The current session to connect to the database.
            checklist (ChecklistModel): The model used with the request.

        Returns:
            Literal[0] | Literal[1]
        """
        try:
            db.add(checklist)
            db.commit()
            db.refresh(checklist)
            return 0
        except IntegrityError as integrity_exc:
            print("IntegrityError:",integrity_exc)
            return 1
        except Exception as exc: # pylint: disable=W0718
            print(exc)
            return 2

    def _get_checklist(self, db: Session, checklist_name: str) -> list:
        """Get targets from the database.
        
        Args:
            db (Session): The current session to connect to the database.

        Returns:
            List[TargetModel]
        """
        checklists: List = []
        try:
            records: List[ChecklistModel] = db.query(ChecklistModel)\
                .filter(ChecklistModel.active == True)\
                .filter_by(name=checklist_name)\
                .order_by(ChecklistModel.category_order,ChecklistModel.item_id)\
                .all()
            for record in records:
                checklist_record = {
                    'item_id': record.item_id,
                    'item_name': record.item_name,
                    'item_category': record.useful_tools
                }
                checklists.append(checklist_record)
        except Exception as exc: # pylint: disable=W0718
            print(exc)
        return checklists

    def _delete_targetnote(self, db: Session, targetnote_id) -> Literal[0] | Literal[1]:
        """Delete a targetnote from the database.
        
        Args:
            db (Session): The current session to connect to the database.
            targetnote_id: The id of the targetnote.

        Returns:
            Literal[0] | Literal[1]
        """
        try:
            record_to_delete: TargetNoteModel | None = db.query(TargetNoteModel).filter_by(id=targetnote_id).first()
            if record_to_delete:
                db.delete(record_to_delete)
                db.commit()
                print("Target note deleted successfully.")
            else:
                print("Target note not found.")
            return 0
        except Exception as exc: # pylint: disable=W0718
            print(exc)
            return 2


    def _get_proxy_history(self, db: Session) -> list:
        """Get proxy history for a target from the database.
        
        Args:
            db (Session): The current session to connect to the database.

        Returns:
            List[ProxyModel]
        """
        proxy_histories: List[ProxyModel] = []

        try:
            if self.parent_obj is not None:
                selected_target = self.parent_obj.selected_target_obj
                if selected_target is not None:
                    hosts = []
                    in_scope_items = self.parent_obj.selected_target_in_scope
                    for item in in_scope_items:
                        hosts.append(item['fqdn'])
                        records: List[ProxyModel] = db.query(ProxyModel).order_by(ProxyModel.created_timestamp).filter_by(host=item['fqdn']).all()
                        for record in records:
                            proxy_record = {
                                'target': selected_target['id'],
                                'id': record.id,
                                'action': record.action,
                                'status': record.response_status_code,
                                'method': record.method,
                                'url':record.full_url,
                                'content':record.content,
                                'text':record.response_text
                            }
                            proxy_histories.append(proxy_record)

        except Exception as exc: # pylint: disable=W0718
            print(exc)
        return proxy_histories

    def tables(self) -> None:
        """Print list of tables in the database.

        Returns:
            None
        """
        with Database._get_db() as db:
            records: Result[Any] = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"))

            print()
            table = Table(title='Tables')
            table.add_column('#')
            table.add_column('Table Name')

            counter = 0
            for record in records:
                table.add_row(str(counter), record[0])
                counter += 1
            
            console = Console()
            console.print(table)
            print()

    def setup(self) -> None:
        """Create tables in the database.

        Returns:
           None
        """
        Base.metadata.create_all(self.engine)

        data: list[ChecklistModel] = SetupData().get_owasp_wstg_checklist()

        with Database._get_db() as db:
            counter = 0
            for checklist_item in data:
                try:
                    db.add(checklist_item)
                    db.commit()
                    db.refresh(checklist_item)
                except IntegrityError:
                    continue
                except Exception as database_exception: # pylint: disable=W0718
                    if 'UniqueViolation' in str(database_exception):
                        continue
                    else:
                        print()
                        print(counter, database_exception)
                counter += 1

        print("\nSetup complete.\n")
