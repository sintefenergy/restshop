from pyshop import ShopSession
from fastapi import HTTPException
import datetime as dt
from typing import Callable, List, Dict
import requests

class UserSession:

    def __init__(self, username: str, expires: dt.datetime):
        self.username: str = username
        self.expires: dt.datetime = expires
        self.shop_sessions: Dict[int, ShopSession] = {}
        self.shop_sessions_time_resolution_is_set: Dict[int, bool] = {}
        self.session_counter: int = 0

    
    def add_shop_session(self, session_name: str, logging_callback: Callable = None, logging_callback_id: str = '', log_file: str = '') -> ShopSession:

        """
            The signature of the callback is shown by example
                def callback(msg, id):
                    print(f'{msg} : {id}')
                    return None
        """

        self.session_counter += 1

        new_shop_session = None
        if logging_callback:
            new_shop_session = ShopSession(license_path='', silent=True, log_file=log_file, name=session_name, id=self.session_counter)
            new_shop_session.shop_api.RegisterCallback(logging_callback, logging_callback_id)
        else:
            new_shop_session = ShopSession(license_path='', silent=False, log_file=log_file, name=session_name, id=self.session_counter)

        self.shop_sessions[self.session_counter] = new_shop_session
        self.shop_sessions_time_resolution_is_set[self.session_counter] = False
        return new_shop_session

    def remove_shop_session(self, session_id: int) -> bool:
        if session_id in self.shop_sessions:
            shop_session = self.shop_sessions.pop(session_id)
            del shop_session
            return True
        else:
            return False

    def update_expiry_time(self, expires: dt.datetime):
        self.expires = expires
        dt.datetime.utcnow()


class SessionManager:

    user_sessions: Dict[str, UserSession] = {}
    logging_endpoint: str = ''

    @staticmethod
    def log_callback(msg, level, id):

        endpoint = SessionManager.logging_endpoint
        # endpoint = endpoint if endpoint else 'http://host.docker.internal:5000/log/message'
        if endpoint:
            try:
                resp = requests.post(
                    endpoint,
                    json={
                        'level': level,
                        'message': msg,
                        'id': id
                    }
                )
                if resp.status_code != 200:
                    print(f'logging endpoint is complaining')
                    print(f'response: {resp}')

            except Exception as e:
                print(f'failed to forward log message to endpoint: {endpoint}')
                print(f' --- exception: {e}')

        return None


    @staticmethod
    def get_user_sessions() -> Dict[str, UserSession]:
        return SessionManager.user_sessions

    @staticmethod
    def add_user_session(username: str, expires) -> UserSession:
        SessionManager.user_sessions[username] = UserSession(username, expires)
        return SessionManager.user_sessions[username]

    @staticmethod
    def remove_user_session(username) -> bool:
        if username in SessionManager.user_sessions:
            SessionManager.user_sessions.pop(username)
            return True
        else:
            return False

    @staticmethod
    def get_user_session(username: str) -> UserSession:
        if username in SessionManager.user_sessions:
            return SessionManager.user_sessions[username]
        else:
            return None

    @staticmethod
    def get_shop_sessions(username: str) -> Dict[int, ShopSession]:
        us = SessionManager.get_user_session(username)
        if us:
            return us.shop_sessions
        else:
            return []

    @staticmethod
    def get_shop_session(username: str, session_id: int) -> ShopSession:

        try:
            us = SessionManager.get_user_session(username)
        except Exception:
            raise HTTPException(400, f'User {{{username}}} does not exist.')

        try:
            sess = us.shop_sessions[session_id]
        except:
            raise HTTPException(400, f'Session {{{session_id}}} does not exist.')

        return sess

    @staticmethod
    def add_shop_session(username: str, session_name: str, log_file: str = '') -> ShopSession:
        us = SessionManager.get_user_session(username)
        if us:
            return us.add_shop_session(session_name, SessionManager.log_callback, f'{username}:{session_name}', log_file)
        else:
            return None

    @staticmethod
    def remove_shop_session(username: str, session_id: int) -> bool:
        us = SessionManager.get_user_session(username)
        if us:
            return us.remove_shop_session(int(session_id))
        else:
            return False

    @staticmethod
    def cleanup_user_sessions() -> None:
        for user in SessionManager.get_user_session_list():
            us = SessionManager.get_user_session(user)
            if dt.datetime.utcnow() > us.expires:
                SessionManager.remove_user_session(user)

    @staticmethod
    def update_expiry_time(username: str, expires: dt.datetime) -> None:
        us = SessionManager.get_user_session(username)
        us.update_expiry_time(expires)
    
    @staticmethod
    def get_model_object_generator(username: str, session_id: int, object_type: str):
        model = SessionManager.get_shop_session(username, session_id).model
        if object_type not in model._all_types:
            raise HTTPException(400, f'object_type {{{object_type}}} is not implemented.')
        return model[object_type]
            
    @staticmethod
    def get_model_object_instance(username: str, session_id: int, object_type: str, object_name: str):
        model_object_generator = SessionManager.get_model_object_generator(username, session_id, object_type)
        if object_name not in model_object_generator._names:
            raise HTTPException(400, f'object_name {{{object_name}}} is not an instance of object_type {{{object_type}}}.')
        return model_object_generator[object_name]