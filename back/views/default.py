import datetime
from pyramid.view import view_config
from pyramid.response import Response

from sqlalchemy.exc import DBAPIError
from ..utils import get_passphrase
from .. import models
from pyramid.security import forget
from pyramid.security import remember
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound,
)


def get_iso_date():
    return datetime.datetime.utcnow().strftime('%Y-%m-%d')


def parse_iso_date(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


def marker_to_dict(marker, user_id):
    return {
        'id': marker.id,
        'lon': float(marker.longitude),
        'lat': float(marker.latitude),
        'name': marker.name,
        'note': marker.note,
        'reported_date': marker.reported_date.strftime('%Y-%m-%d'),
        'owned': marker.user_id == user_id,
    }


@view_config(route_name='home', renderer='../templates/index.jinja2')
def home(request):
    raise ValueError()
    return {'isotoday': get_iso_date(),
            'gen_passphrase': get_passphrase()}


@view_config(route_name='home', renderer='../templates/index.jinja2', request_method='POST')
def home_post(request):

    passphrase = request.params['passphrase']
    passphrase = passphrase.strip()

    gen_passphrase = request.params['gen_passphrase']
    email = request.params['email']

    # Check if too short
    if len(passphrase) <= 16:
        print("pass too short")
        return {'isotoday': get_iso_date(),
                'gen_passphrase': get_passphrase()}

    if gen_passphrase == passphrase:
        print("pass is the same as generated pass - adding user")
        # Check if the generated pass was entered
        new_user = models.User(passphrase=passphrase, email=email)
        request.dbsession.add(new_user)
        request.dbsession.flush()

        headers = remember(request, new_user.id)
        return HTTPFound(location=request.route_url('add_marker'),
                         headers=headers)
    else:
        print("pass is different than generated - search user")
        # Try to existing find a user with passphrase
        user = request.dbsession.query(models.User).filter_by(
            passphrase=passphrase).first()

        if user is not None:
            print("found")
            # Check if user has email and if new email was provided
            if email:
                user.email = email
                request.dbsession.flush()
            # Found previous user
            headers = remember(request, user.id)
            return HTTPFound(location=request.route_url('add_marker'),
                             headers=headers)
        else:
            print("not found")

    return {'isotoday': get_iso_date(),
            'gen_passphrase': get_passphrase()}


@view_config(route_name='add_marker', renderer='../templates/add_marker.jinja2')
def add_marker(request):
    if not request.authenticated_userid:
        raise HTTPForbidden()

    return {'isotoday': get_iso_date()}


@view_config(route_name='add_marker', xhr=True, renderer='json', request_method='POST')
def add_marker_post(request):

    if not request.authenticated_userid:
        raise HTTPForbidden()

    latitude = request.params.get('lat')
    longitude = request.params.get('lon')
    name = request.params.get('name')
    note = request.params.get('note')
    reported_date = parse_iso_date(request.params.get('reported_date'))

    new_marker = models.Marker(
        latitude=latitude,
        longitude=longitude,
        name=name,
        note=note,
        reported_date=reported_date,
        user_id=request.authenticated_userid,
    )

    request.dbsession.add(new_marker)
    # Needed to get the ID
    request.dbsession.flush()

    return marker_to_dict(new_marker, request.authenticated_userid)


@view_config(route_name='remove_marker', xhr=True, renderer='json')
def remove_marker(request):
    marker_id = int(request.matchdict.get('marker_id'))
    markers_to_delete = request.dbsession.query(models.Marker).filter_by(
        id=marker_id,
        user_id=request.user_id,
    )

    markers_to_delete.deleted = True
    request.dbsession.commit()

    return {}


@view_config(route_name='list_markers', renderer='json')
def list_markers(request):
    min_date = request.params.get("min_date")
    max_date = request.params.get("max_date")

    db_markers = request.dbsession.query(models.Marker)

    if min_date is not None:
        db_markers = db_markers.filter(reported_date >= min_date)
    if max_date is not None:
        db_markers = db_markers.filter(reported_date <= max_date)

    return [marker_to_dict(m, request.authenticated_userid) for m in db_markers]


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    url = request.route_url('home')
    print("logged out")
    return HTTPFound(location=url, headers=headers)


@view_config(context=Exception)
def system_error_view(context, request):
    request.raven.captureException()
