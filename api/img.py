from flask import make_response

from reptile.SQL import SQL, imgs, comm_img

def get_img(imgid):
    db = SQL('datadb')

    imgdata = db.session.query(imgs).filter(imgs.id == imgid).first().img

    response = make_response(imgdata)
    response.headers['Content-Type'] = 'image/png'
    db.close()

    return response


def get_comm_img(imgid):
    db = SQL('datadb')

    imgdata = db.session.query(comm_img).filter(comm_img.id == imgid).first().img

    response = make_response(imgdata)
    response.headers['Content-Type'] = 'image/png'
    db.close()

    return response