# -*- coding: UTF-8 -*-
from __future__ import print_function

from gi.repository import Gtk, GObject

from pychess.Savers import database, pgn, fen, epd
from pychess.System.protoopen import protoopen
from pychess.Utils.const import DRAW, LOCAL, WHITE, BLACK, WAITING_TO_START, reprResult
from pychess.Players.Human import Human
from pychess.widgets.ionest import game_handler
from pychess.Utils.GameModel import GameModel
from pychess.perspectives import perspective_manager


class GameList(Gtk.TreeView):

    STEP = 50

    def __init__(self, uri):
        GObject.GObject.__init__(self)

        self.offset = 0

        self.liststore = Gtk.ListStore(int, str, str, str, str, str, str, str,
                                       str, str, str, str, str, str)
        self.modelsort = Gtk.TreeModelSort(self.liststore)

        self.modelsort.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.set_model(self.modelsort)
        self.get_selection().set_mode(Gtk.SelectionMode.BROWSE)
        self.set_headers_visible(True)
        self.set_rules_hint(True)
        self.set_search_column(1)

        cols = (_("Id"), _("White"), _("W Elo"), _("Black"), _("B Elo"),
                _("Result"), _("Event"), _("Site"), _("Round"), _("Date"),
                "ECO", "TC", "Variant", "FEN")
        for i, col in enumerate(cols):
            r = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col, r, text=i)
            column.set_resizable(True)
            column.set_reorderable(True)
            column.set_sort_column_id(i)
            column.connect("clicked", self.column_clicked, i)
            self.append_column(column)

        self.connect("row-activated", self.row_activated)

        self.set_cursor(0)
        self.columns_autosize()
        self.gameno = 0
        self.uri = uri

        if self.uri.endswith(".pdb"):
            self.chessfile = database.load(open(self.uri))
        elif self.uri.endswith(".pgn"):
            self.chessfile = pgn.load(protoopen(self.uri))
        elif self.uri.endswith(".epd"):
            self.chessfile = epd.load(open(self.uri))
        elif self.uri.endswith(".fen"):
            self.chessfile = fen.load(open(self.uri))

        self.chessfile.build_query()
        self.load_games()

        hbox = Gtk.HBox()

        self.playerlist = Gtk.ListStore(str)

        self.match = set()
        completion = Gtk.EntryCompletion()
        completion.set_model(self.playerlist)
        completion.set_text_column(0)

        for player in self.chessfile.players:
            self.playerlist.append(player)

        entry = Gtk.Entry()
        entry.set_completion(completion)
        entry.connect('activate', self.activate_entry)

        hbox.pack_start(entry, False, False, 0)

        toolbar = Gtk.Toolbar()
        hbox.pack_start(toolbar, True, True, 0)

        firstButton = Gtk.ToolButton(Gtk.STOCK_MEDIA_PREVIOUS)
        toolbar.insert(firstButton, -1)

        prevButton = Gtk.ToolButton(Gtk.STOCK_MEDIA_REWIND)
        toolbar.insert(prevButton, -1)

        nextButton = Gtk.ToolButton(Gtk.STOCK_MEDIA_FORWARD)
        toolbar.insert(nextButton, -1)

        lastButton = Gtk.ToolButton(Gtk.STOCK_MEDIA_NEXT)
        toolbar.insert(lastButton, -1)

        firstButton.connect("clicked", self.on_first_clicked)
        prevButton.connect("clicked", self.on_prev_clicked)
        nextButton.connect("clicked", self.on_next_clicked)
        lastButton.connect("clicked", self.on_last_clicked)

        self.vbox = Gtk.VBox()
        self.vbox.pack_start(hbox, False, False, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.add(self)
        self.vbox.pack_start(sw, True, True, 0)
        self.vbox.show_all()

    def activate_entry(self, entry):
        text = entry.get_text()
        self.chessfile.build_where(text)
        self.offset = 0
        self.chessfile.build_query()
        self.load_games()

    def on_first_clicked(self, widget):
        self.offset = 0
        self.load_games()

    def on_prev_clicked(self, widget):
        if self.offset - self.STEP >= 0:
            self.offset = self.offset - self.STEP
            self.load_games()

    def on_next_clicked(self, widget):
        if self.offset + self.STEP <= self.chessfile.count:
            self.offset = self.offset + self.STEP
            self.load_games()

    def on_last_clicked(self, widget):
        self.offset = (self.chessfile.count // self.STEP) * self.STEP
        self.load_games()

    def column_clicked(self, col, data):
        self.set_search_column(data)

    def load_games(self):
        self.liststore.clear()

        getTag = self.chessfile._getTag
        getResult = self.chessfile.get_result
        getPlayers = self.chessfile.get_player_names
        add = self.liststore.append

        self.chessfile.get_records(self.offset, self.STEP)
        print("got %s recors" % len(self.chessfile.games))

        self.id_list = []
        for i in range(len(self.chessfile.games)):
            game_id = self.chessfile.get_id(i)
            self.id_list.append(game_id)
            wname, bname = getPlayers(i)
            welo = getTag(i, "WhiteElo")
            belo = getTag(i, "BlackElo")
            result = getResult(i)
            result = "½-½" if result == DRAW else reprResult[result]
            event = getTag(i, 'Event')
            site = getTag(i, 'Site')
            round_ = getTag(i, "Round")
            date = getTag(i, "Date")
            eco = getTag(i, "ECO")
            tc = getTag(i, "TimeControl")
            variant = getTag(i, "Variant")
            fen = getTag(i, "FEN")
            add([game_id, wname, welo, bname, belo, result, event, site,
                 round_, date, eco, tc, variant, fen])
        self.set_cursor(0)

    def row_activated(self, widget, path, col):
        # print(self.modelsort.convert_path_to_child_path(path)[0])
        game_id = self.liststore[self.modelsort.convert_path_to_child_path(
            path)[0]][0]
        print("game_id=%s" % game_id)
        gameno = self.id_list.index(game_id)
        print("gameno=%s" % gameno)

        gamemodel = GameModel()

        variant = self.chessfile.get_variant(gameno)
        if variant:
            gamemodel.tags["Variant"] = variant

        wp, bp = self.chessfile.get_player_names(gameno)
        p0 = (LOCAL, Human, (WHITE, wp), wp)
        p1 = (LOCAL, Human, (BLACK, bp), bp)
        self.chessfile.loadToModel(gameno, -1, gamemodel)

        gamemodel.status = WAITING_TO_START
        game_handler.generalStart(gamemodel, p0, p1)

        perspective_manager.activate_perspective("games")
