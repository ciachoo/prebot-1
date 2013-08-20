#
# PreBot IRC bot software
# (c) Michal Kuchta 2013
#

from event import handler
from storage import db
from httpd import menulink, get, post
from util import _networks
import logging
from irc import UserInfo


def _calcWeight(str, weight):
    """
        Calculate weight of one hostname part for the user.
    """

    # remove quoted wildcard chars, does not meen a difference.
    str = str.replace("%%", "-").replace("__", "-")

    # calc wildcards
    wc = str.count("%") + str.count("_")
    if wc > 10:
        wc = 10

    # calc other chars
    return float(len(str) - wc) * float(weight) + (wc / 10.0)


def init():
    c = db.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "   name TEXT, "
        "   password TEXT"
        ")")

    c.execute(
        "CREATE TABLE IF NOT EXISTS user_hosts ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "   user_id INT, "
        "   nick TEXT, "
        "   user TEXT, "
        "   host TEXT, "
        "   FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE"
        ")")

    c.execute(
        "CREATE TABLE IF NOT EXISTS user_flags ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "   user_id INT, "
        "   network TEXT NULL DEFAULT NULL, "
        "   channel TEXT NULL DEFAULT NULL, "
        "   flag TEXT, "
        "   value INT, "
        "   FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE, "
        "   UNIQUE (user_id, network, channel, flag)"
        ")")

    db.create_function("user_calcWeight", 2, _calcWeight)


class User:
    def __init__(self):
        self.id = None
        self.name = None
        self.password = None

    def loadFromRow(self, row):
        for key, val in row.iteritems():
            if key in self.__dict__:
                self.__dict__[key] = val

    def hasHostname(self, nick, user, host):
        c = db.cursor()
        c.execute("SELECT 1 FROM user_hosts WHERE user_id = ? AND ? LIKE nick AND ? LIKE user AND ? LIKE host", (self.id, nick, user, host))
        row = c.fetchone()
        if row:
            return True
        else:
            return False

    def hasFlag(self, flag, channel=None, network=None):
        c = db.cursor()

        query = "SELECT value FROM user_flags WHERE user_id = ? AND flag = ? AND " + condChannel + " AND " + condNetwork
        queryValues = [self.id, flag]

        if channel is not None:
            condChannel = "(channel IS NULL OR channel = ?)"
            queryValues.append(channel)
        else:
            condChannel = "(channel IS NULL)"

        if network is not None:
            condNetwork = "(network IS NULL OR network = ?)"
            queryValues.append(network)
        else:
            condNetwork = "(network IS NULL)"

        query += " ORDER BY network DESC, channel DESC LIMIT 1"

        c.execute(query, tuple(queryValues))
        row = c.fetchone()
        if row:
            return True if row["value"] == 1 else False
        else:
            return False

    @staticmethod
    def _wildcardToLike(str):
        return str.replace("%", "%%").replace("_", "__").replace("*", "%").replace("?", "_")

    @staticmethod
    def _likeToWildcard(str):
        return str.replace("%", "*").replace("_", "?").replace("??", "_").replace("**", "%")

    def listHostnames(self):
        c = db.cursor()
        c.execute("SELECT id, nick, user, host FROM user_hosts WHERE user_id = ?", (self.id, ))
        return [{
            "id": row["id"],
            "host": "%s!%s@%s" % (
                self._likeToWildcard(row["nick"]),
                self._likeToWildcard(row["user"]),
                self._likeToWildcard(row["host"]))
        } for row in c.fetchall()]

    def addHostname(self, nick, user, host):
        c = db.cursor()
        c.execute("INSERT INTO user_hosts (user_id, nick, user, host) VALUES (?, ?, ?, ?)", (
            self.id,
            self._wildcardToLike(nick),
            self._wildcardToLike(user),
            self._wildcardToLike(host)))
        db.commit()

    def modifyHostname(self, id, nick, user, host):
        c = db.cursor()
        c.execute("UPDATE user_hosts SET nick = ?, user = ?, host = ? WHERE id = ? AND user_id = ?", (nick, user, host, id, self.id))
        db.commit()

    def delHostname(self, id):
        c = db.cursor()
        c.execute("DELETE FROM user_hosts WHERE id = ? AND user_id = ?", (id, self.id))
        db.commit()

    def listFlags(self):
        c = db.cursor()
        c.execute("SELECT id, network, channel, flag, value FROM user_flags WHERE user_id = ? ORDER BY network ASC, channel ASC, flag ASC", (self.id, ))
        return [{
            "id": row["id"],
            "network": row["network"],
            "channel": row["channel"],
            "flag": row["flag"],
            "value": True if row["value"] else False
        } for row in c.fetchall()]

    def setFlag(self, flag, value, channel=None, network=None):
        c = db.cursor()
        c.execute("INSERT OR REPLACE INTO user_flags (user_id, flag, value, network, channel) VALUES (?, ?, ?, ?, ?)", (
            self.id,
            flag,
            1 if value else 0,
            network,
            channel))
        db.commit()

    def remFlag(self, id):
        c = db.cursor()
        c.execute("DELETE FROM user_flags WHERE id = ? AND user_id = ?", (id, self.id))
        db.commit()

    @staticmethod
    def findById(id):
        c = db.cursor()
        c.execute("SELECT id, name, password FROM users WHERE id = ?", (id, ))
        row = c.fetchone()
        if row:
            u = User()
            u.loadFromRow(row)
            return u
        else:
            return None

    @staticmethod
    def findByHost(nick, user, host):
        c = db.cursor()
        c.execute("SELECT u.id AS id, u.name AS name, u.password AS password FROM user_hosts uh LEFT JOIN users u ON (u.id = uh.user_id) WHERE ? LIKE nick AND ? LIKE user AND ? LIKE host ORDER BY user_calcWeight(nick, 200) + user_calcWeight(user, 100) + user_calcWeight(password, 1) DESC LIMIT 1", (self.id, nick, user, host))
        row = c.fetchone()
        if row:
            u = User()
            u.loadFromRow(row)
            return u
        else:
            return None


@handler("irc.join")
def ev_join(eventData, handlerData):
    pass


@handler("irc.op")
def ev_op(eventData, handlerData):
    pass


@handler("irc.deop")
def ev_deop(eventData, handlerData):
    pass


@handler("irc.voice")
def ev_voice(eventData, handlerData):
    pass


@handler("irc.devoice")
def ev_devoice(eventData, handlerData):
    pass


@handler("irc.opped")
def ev_opped(eventData, handlerData):
    pass


@handler("irc.kick")
def ev_kicked(eventData, handlerData):
    pass


@menulink("Users", "/users")
def web_index(req):
    # List users
    c = db.cursor()

    findHostname = req.get.getfirst("search")
    if findHostname:
        c.execute(
            "SELECT "
            "   u.id AS id, u.name AS name FROM user_hosts uh "
            "LEFT JOIN users u ON (u.id = uh.user_id) "
            "WHERE "
            "   ? LIKE uh.nick "
            "   AND ? LIKE uh.user "
            "   AND ? LIKE uh.host "
            "GROUP BY u.id "
            "ORDER BY u.name ASC")
    else:
        c.execute("SELECT id, name FROM users ORDER BY name ASC")

    users = []
    for row in c.fetchall():
        u = User()
        u.loadFromRow(row)
        users.append(u)

    req.render("/users/index.html", {
        "users": users,
        "search": findHostname
    })


@post("/user.add")
def web_user_add(req):
    name = req.post.getfirst("name")
    c = db.cursor()
    c.execute("INSERT INTO users (name) VALUES (?)", (name, ))
    userId = c.lastrowid
    db.commit()

    req.redirect("/user.show?id=%d" % userId)


@get("/user.show")
def web_user_show(req):
    id = int(req.get.getfirst("id"))
    u = User.findById(id)
    if u is not None:
        # List networks (only connected ones)
        networks = []
        for irc in _networks:
            if irc.networkName:
                networks.append(irc.networkName)

        req.render("/users/show.html", {
            "user": u,
            "networks": networks
        })
    else:
        req.render("/users/notfound.html")


@post("/user.edit")
def web_user_edit(req):
    id = int(req.get.getfirst("id"))
    name = req.post.getfirst("name")

    c = db.cursor()
    c.execute("UPDATE users SET name = ? WHERE id = ?", (id, name))
    db.commit()

    req.redirect("/user.show?id=%d" % id)


@post("/user.host.add")
def web_host_add(req):
    userId = int(req.get.getfirst("userid"))
    host = req.post.getfirst("host")

    u = User.findById(userId)

    nick, user, host = UserInfo.parseAddress(host)
    u.addHostname(nick, user, host)

    req.redirect("/user.show?id=%d" % userId)


@post("/user.flag.add")
def web_flag_add(req):
    userId = int(req.get.getfirst("userid"))

    network = req.post.getfirst("network")
    if network == "":
        network = None

    channel = req.post.getfirst("channel")
    if channel == "" or channel == "*":
        channel = None

    flag = req.post.getfirst("flag")
    if flag == "":
        flag = None

    value = True if req.post.getfirst("value") is not None else False

    u = User.findById(userId)
    if u:
        u.setFlag(flag, value, network=network, channel=channel)

    req.redirect("/user.show?id=%d" % userId)

init()