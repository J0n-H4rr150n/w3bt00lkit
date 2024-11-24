"""db.py"""
from typing import Any, List, Literal
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from sqlalchemy import Engine, Result, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import pandas as pd
from models import Base, ChecklistModel, ProxyModel, TargetModel, TargetNoteModel, TargetScopeModel
from models.setupdata import SetupData
from .common import word_completer

# pylint: disable=C0121

class Database():
    """Database."""
    def __init__(self, parent_obj=None) -> None:
        self.parent_obj = parent_obj
        self.engine: Engine = create_engine('postgresql://w3bt00lkit:w3bt00lkit@localhost:5432/w3bt00lkit')
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.name = 'database'
        self.session = PromptSession()
        self.completer: WordCompleter = word_completer(self)

    def _add_request(self, db: Session, request: ProxyModel) -> ProxyModel:
        """Add request to the database.
        
        Args:
            db (Session): The current session to connect to the database.
            request (ProxyModel): The model used with the request.

        Returns:
           request (ProxyModel): The updated model that was used with the request.
        """
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

    def _add_target(self, db: Session, target: TargetModel) -> Literal[0] | Literal[1]:
        """Add target to the database.
        
        Args:
            db (Session): The current session to connect to the database.
            target (TargetModel): The model used with the request.

        Returns:
            Literal[0] | Literal[1]
        """
        try:
            db.add(target)
            db.commit()
            db.refresh(target)
            return 0
        except IntegrityError:
            return 1
        except Exception as exc: # pylint: disable=W0718
            print(exc)
            return 2

    def _get_targets(self, db: Session) -> list:
        """Get targets from the database.
        
        Args:
            db (Session): The current session to connect to the database.

        Returns:
            List[TargetModel]
        """
        targets: List[TargetModel] = []
        try:
            records: List[TargetModel] = db.query(TargetModel).filter(TargetModel.active == True).order_by(TargetModel.name).all()
            for record in records:
                target_record = {
                    'id': record.id,
                    'name': record.name,
                    'platform': record.platform
                }
                targets.append(target_record)
        except Exception as exc: # pylint: disable=W0718
            print(exc)
        return targets

    def _add_targetscope(self, db: Session, targetscope: TargetScopeModel) -> Literal[0] | Literal[1]:
        """Add targetscope to the database.
        
        Args:
            db (Session): The current session to connect to the database.
            targetscope (TargetScopeModel): The model used with the request.

        Returns:
            Literal[0] | Literal[1]
        """
        try:
            db.add(targetscope)
            db.commit()
            db.refresh(targetscope)
            return 0
        except IntegrityError as integrity_exc:
            print("Integrity Error:", integrity_exc)
            return 1
        except Exception as exc: # pylint: disable=W0718
            print(exc)
            return 2

    def _add_targetnote(self, db: Session, targetnote: TargetNoteModel) -> Literal[0] | Literal[1]:
        """Add targetnote to the database.
        
        Args:
            db (Session): The current session to connect to the database.
            targetnote (TargetNoteModel): The model used with the request.

        Returns:
            Literal[0] | Literal[1]
        """
        try:
            db.add(targetnote)
            db.commit()
            db.refresh(targetnote)
            return 0
        except IntegrityError as integrity_exc:
            print("Integrity Error:", integrity_exc)
            return 1
        except Exception as exc: # pylint: disable=W0718
            print(exc)
            return 2

    def _get_targetnotes(self, db: Session) -> list:
        """Get target notes from the database.
        
        Args:
            db (Session): The current session to connect to the database.

        Returns:
            List[TargetNoteModel]
        """
        targetnotes: List[TargetNoteModel] = []

        try:
            if self.parent_obj is not None:
                selected_target = self.parent_obj.selected_target_obj
                if selected_target is not None:
                    records: List[TargetNoteModel] = db.query(TargetNoteModel).filter(TargetNoteModel.active == True)\
                        .filter_by(target_id=selected_target['id'])\
                        .order_by(TargetNoteModel.created_timestamp).all()
                    for record in records:
                        tmp_full_note = record.full_note
                        if len(tmp_full_note) > 500:
                            tmp_full_note = tmp_full_note[:500] + " ..."
                        targetnote_record = {
                            'id': record.id,
                            'target_id': record.target_id,
                            'created': record.created_timestamp,
                            'modified': record.modified_timestamp,
                            'fqdn': record.fqdn,
                            'path': record.path,
                            'url': record.url,
                            'page': record.page,
                            'summary': tmp_full_note,
                            'full_note': record.full_note
                        }
                        targetnotes.append(targetnote_record)
        except Exception as exc: # pylint: disable=W0718
            print(exc)
        return targetnotes

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
        db: Session = self.session_local()
        records: Result[Any] = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"))
        tables: list = []
        for record in records:
            tables.append({'Name':record[0]})
        df = pd.DataFrame(tables)
        print(df)

    def setup(self) -> None:
        """Create table in the database.

        Returns:
           None
        """
        Base.metadata.create_all(self.engine)

        data: list[ChecklistModel] = SetupData().get_owasp_wstg_checklist()
        try:
            db_session: Session = self.session_local()
            counter = 0
            for checklist_item in data:
                result: Literal[0] | Literal[1] = self._add_checklist(db_session, checklist_item) # pylint: disable=W0212
                if result == 0:
                    print(f"Checklist item {counter} added to the database.")
                elif result == 1:
                    print(f"Checklist item {counter} already exists.")
                else:
                    print(f"There was an error trying to add the checklist item {counter}.")
                counter += 1
        except Exception as database_exception: # pylint: disable=W0718
            print(database_exception)
