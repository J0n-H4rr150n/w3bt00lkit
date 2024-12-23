"""db.py"""
import os
from contextlib import contextmanager
from typing import Any, Generator, List, Literal
from sqlalchemy import Engine, Result, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from rich.console import Console
from rich.table import Table
from models import Base, ChecklistModel, ProxyModel, TargetNoteModel, VulnerabilityModel
from models.setupdata import SetupData

# pylint: disable=C0121,C0301,W0718
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CONNECTION_STRING_POSTGRES = 'postgresql://w3bt00lkit:w3bt00lkit@localhost:5432/w3bt00lkit?gssencmode=disable'
CONNECTION_STRING_SQLITE = f'sqlite:///{BASE_PATH}w3bt00lkit.db'
#CONNECTION_OPTION = 'sqlite'
CONNECTION_OPTION = 'postgres'

class Database():
    """Database."""
    def __init__(self, app_obj, args) -> None:
        self.app_obj = app_obj
        self.args = args
        self.engine_postgres: Engine = create_engine(CONNECTION_STRING_POSTGRES, connect_args={'options': '-c statement_timeout=5000'})
        self.engine_sqlite: Engine = create_engine(CONNECTION_STRING_SQLITE)
        if CONNECTION_OPTION == 'sqlite':
            self.engine = self.engine_sqlite
        else:
            self.engine = self.engine_postgres
        self.db_session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def _get_db() -> Generator[Session, Any, None]: # pylint: disable=E0211
        """Get database."""
        if CONNECTION_OPTION == 'sqlite':
            engine: Engine = create_engine(CONNECTION_STRING_SQLITE)
        else:
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

    def _get_proxy_history(self, db: Session) -> list:
        """Get proxy history for a target from the database.
        
        Args:
            db (Session): The current session to connect to the database.

        Returns:
            List[ProxyModel]
        """
        proxy_histories: List[ProxyModel] = []

        try:
            if self.app_obj is not None:
                selected_target = self.app_obj.selected_target_obj
                if selected_target is not None:
                    hosts = []
                    in_scope_items = self.app_obj.selected_target_in_scope
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

        if data is not None:
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
                        print()
                        print(counter, database_exception)
                    counter += 1

        vulnerabilities: List[VulnerabilityModel] = SetupData().get_vulnerabilities()

        if vulnerabilities is not None:
            with Database._get_db() as db:
                for vulnerability in vulnerabilities:
                    try:
                        db.add(vulnerability)
                        db.commit()
                        db.refresh(vulnerability)
                    except IntegrityError:
                        continue
                    except Exception as database_exception: # pylint: disable=W0718
                        if 'UniqueViolation' in str(database_exception):
                            continue
                        print()
                        print(database_exception)

        print("\nSetup complete.\n")
