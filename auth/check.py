from index import login_manager
import reptile.SQL as db

@login_manager.request_loader
def load_user_from_request(request):
    # try to login using the api_key url arg
    session_id = request.args.get('session_id')
    if session_id:
        SQL = db.SQL('webdb')
        user = SQL.session.query(db.User).filter_by(loginkey=session_id).first()
        SQL.close()
    if user:
        return user
    # return None if both methods did not login the user
    return None


@login_manager.user_loader
def load_user(session_id):
    if session_id:
        SQL = db.SQL('webdb')
        user = SQL.session.query(db.User).filter_by(loginkey=session_id).first()
        SQL.close()
    if user:
        return user
    # return None if both methods did not login the user
    return None
