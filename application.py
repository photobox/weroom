from flask import Flask, request, redirect, make_response, url_for, flash, render_template
app = Flask('test', template_folder='/home/sbourigault/PycharmProjects/WeRoom/templates')
app.secret_key = 'ohyeah'

from client import Client

@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        print(request.form)
        username=request.form.get('email')
        pwd=request.form.get('password')
        cli = Client()
        if not cli.login(username, pwd):
            flash('Couldn\'t connect to wework')
            return redirect(url_for('main'))

        date=str(request.form.get('date'))
        start=str(request.form.get('start_time'))
        end=str(request.form.get('end_time'))

        possible_rooms = request.form.get('possible_rooms')
        if not possible_rooms:
            possible_rooms=None
            whiteboard='whiteboard' in request.form
            tv='tv' in request.form
            min_capcity=int(request.form.get('min_capacity'))
            floor=int(request.form.get('floor'))
        else:
            whiteboard = None
            tv = None
            min_capcity = None
            floor = None
            possible_rooms=possible_rooms.split(',')
        times=int(request.form.get('times'))
        period=int(request.form.get('period'))

        result_log = cli.find_and_book_multiple(date, start, end,
                                                room_list=possible_rooms,
                                                min_capacity=min_capcity, whiteboard=whiteboard, tv=tv,
                                                preferred_floor=floor,
                                                period=period, times=times)
        for r in result_log:
            flash(r)
        r=make_response(redirect(url_for('main')))
        return r
    return render_template('tmp.html')

