"""
Island Adventures — Kivy/Android версия
Управление: экранный джойстик (крестовина)
"""
import os, sys, json, time, random, math
from functools import partial

os.environ.setdefault('KIVY_NO_ENV_CONFIG', '1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, Ellipse, Line, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.utils import platform
from kivy.metrics import dp, sp

# ─── Пути ────────────────────────────────────────────────────
def res(name):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'assets', name)

if platform == 'android':
    from android.storage import app_storage_path
    SAVE_DIR = app_storage_path()
else:
    SAVE_DIR = os.path.expanduser('~')

def slot_path(n): return os.path.join(SAVE_DIR, f'island_adv_slot{n}.json')
SETTINGS_FILE = os.path.join(SAVE_DIR, 'island_adv_settings.json')

# ─── Загадки ─────────────────────────────────────────────────
RIDDLES = [
    {"name":"Идол №1 — Дух Времени","img":"riddle_1.png",
     "text":"В каком месяце болтливая девочка говорит меньше всего?",
     "answer":"февраль","part_name":"Колесо шасси","part_icon":"part_1.png",
     "hint":"Подумай о длине месяца..."},
    {"name":"Идол №2 — Дух Загадки","img":"riddle_2.png",
     "text":"На поляне 3 сундука.\nСундук 1: Запчасть здесь\nСундук 2: Запчасть не в первом\nСундук 3: Запчасть не здесь\nТолько одна надпись правдива. Какой сундук?",
     "answer":"2","part_name":"Штурвал","part_icon":"part_2.png",
     "hint":"Если правдива надпись 1, то надпись 2 ложна..."},
    {"name":"Идол №3 — Дух Мудрости","img":"riddle_3.png",
     "text":"Что в кувшин никогда не влезет,\nкакого бы размера кувшин ни был?",
     "answer":"крышка","part_name":"Кресло пилота","part_icon":"part_3.png",
     "hint":"Что не может поместиться физически?"},
    {"name":"Идол №4 — Дух Тайны","img":"riddle_4.png",
     "text":"Оно принадлежит тебе,\nно другие используют его чаще.",
     "answer":"имя","part_name":"Канистра топлива","part_icon":"part_4.png",
     "hint":"Что люди произносят, обращаясь к тебе?"},
    {"name":"Идол №5 — Дух Ветра","img":"riddle_5.png",
     "text":"Я говорю без рта.\nСлышу без ушей.\nУ меня нет тела.\nНо ветер даёт мне жизнь.",
     "answer":"эхо","part_name":"Воздушный винт","part_icon":"part_5.png",
     "hint":"В горах повторяет твои слова..."},
    {"name":"Идол №6 — Дух Пути","img":"riddle_6.png",
     "text":"Я не дверь, но открываю путь.\nКак выходишь из дома — про меня не забудь.",
     "answer":"ключ","part_name":"Крыло самолёта","part_icon":"part_6.png",
     "hint":"Что берёшь с собой, уходя из дома?"},
    {"name":"Идол №7 — Дух Жизни","img":"riddle_7.png",
     "text":"Что можно держать,\nно невозможно взять в руки?",
     "answer":"дыхание","part_name":"Компас","part_icon":"part_7.png",
     "hint":"Что ты делаешь каждую секунду?"},
    {"name":"Идол №8 — Дух Зеркала","img":"riddle_8.png",
     "text":"Мужчина смотрит на портрет:\n«Нет братьев и сестёр,\nно человек на картине — сын моего отца».\nКем ему приходится человек на портрете?",
     "answer":"я","part_name":"Навигационная карта","part_icon":"part_8.png",
     "hint":"Кто является сыном отца без братьев?"},
    {"name":"Идол №9 — Великий Дух","img":"riddle_9.png",
     "text":"Есть семь факелов.\nКаждый второй потушен.\nКаждый третий зажжён.\nКаждый шестой потушен.\nСколько факелов горит?",
     "answer":"4","part_name":"Реактивный двигатель","part_icon":"part_9.png",
     "hint":"Разбери каждое условие для факелов 1-7..."},
]

IDOL_POS = [
    (0.2209,0.4848),(0.3222,0.3684),(0.3931,0.2990),(0.5949,0.2982),
    (0.6762,0.3581),(0.7695,0.4482),(0.8046,0.5383),(0.7536,0.6132),
    (0.2448,0.5837),
]

KAI_SPEED = 0.005
TRIGGER   = 0.055
RESET     = TRIGGER + 0.04
FPS       = 60

# ─── Настройки / сохранения ──────────────────────────────────
def load_settings():
    try:
        with open(SETTINGS_FILE,'r',encoding='utf-8') as f: return json.load(f)
    except: return {"music":True,"volume":0.6,"hints":True}

def save_settings(d):
    try:
        with open(SETTINGS_FILE,'w',encoding='utf-8') as f: json.dump(d,f)
    except: pass

def load_slot(n):
    try:
        with open(slot_path(n),'r',encoding='utf-8') as f: return json.load(f)
    except: return None

def save_slot(n,data):
    from datetime import datetime
    data['slot_name'] = datetime.now().strftime('%d.%m.%Y %H:%M')
    data['solved_count'] = len(data.get('solved',[]))
    try:
        with open(slot_path(n),'w',encoding='utf-8') as f: json.dump(data,f)
    except: pass

# ─── Цвета ───────────────────────────────────────────────────
def hex2rgba(h):
    h=h.lstrip('#')
    if len(h)==6: r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16); a=255
    else: r,g,b,a=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16),int(h[6:8],16)
    return r/255,g/255,b/255,a/255

GOLD  = hex2rgba('#d4a017')
GOLD2 = hex2rgba('#f0c040')
BROWN = hex2rgba('#6b3a1f')
RED   = hex2rgba('#cc3300')
BG    = hex2rgba('#1a0e00')
PANEL = hex2rgba('#2d1a00')
WHITE = (1,1,1,1)
DIM   = hex2rgba('#9a7a50')

# ════════════════════════════════════════════════════════════
# ВИДЖЕТЫ
# ════════════════════════════════════════════════════════════

class GoldButton(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_color  = hex2rgba('#4a2800')
        self.color             = GOLD2
        self.font_size         = sp(16)
        self.bold              = True
        self.size_hint_y       = None
        self.height            = dp(52)


class GameLabel(Label):
    def __init__(self, **kw):
        kw.setdefault('color', hex2rgba('#f5e6c8'))
        kw.setdefault('font_size', sp(14))
        super().__init__(**kw)


# ════════════════════════════════════════════════════════════
# ДЖОЙСТИК
# ════════════════════════════════════════════════════════════
class Joystick(Widget):
    """Экранная крестовина управления."""
    def __init__(self, on_move=None, **kw):
        super().__init__(**kw)
        self.on_move_cb = on_move
        self.dx = 0; self.dy = 0
        self._touches = {}
        self.size_hint = (None,None)
        self.size = (dp(160), dp(160))
        self._draw()
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *a):
        self.canvas.clear()
        cx,cy = self.center
        r = min(self.width,self.height)*0.5
        with self.canvas:
            # Фон круга
            Color(0,0,0,0.4)
            Ellipse(pos=(cx-r,cy-r), size=(r*2,r*2))
            # Крестовина
            Color(*GOLD, 0.7)
            bw = dp(44); bh = dp(36)
            # Вверх
            RoundedRectangle(pos=(cx-bw/2, cy+r*0.25), size=(bw,bh), radius=[dp(8)])
            # Вниз
            RoundedRectangle(pos=(cx-bw/2, cy-r*0.25-bh), size=(bw,bh), radius=[dp(8)])
            # Влево
            RoundedRectangle(pos=(cx-r*0.25-bh, cy-bw/2), size=(bh,bw), radius=[dp(8)])
            # Вправо
            RoundedRectangle(pos=(cx+r*0.25, cy-bw/2), size=(bh,bw), radius=[dp(8)])
            # Стрелки
            Color(1,1,1,0.9)
            # ▲
            ax,ay = cx, cy+r*0.25+bh*0.5
            Line(points=[ax,ay-dp(8),ax-dp(8),ay+dp(6),ax+dp(8),ay+dp(6)], width=dp(2))
            # ▼
            ax,ay = cx, cy-r*0.25-bh*0.5
            Line(points=[ax,ay+dp(8),ax-dp(8),ay-dp(6),ax+dp(8),ay-dp(6)], width=dp(2))
            # ◄
            ax,ay = cx-r*0.25-bh*0.5, cy
            Line(points=[ax+dp(8),ay+dp(8),ax-dp(6),ay,ax+dp(8),ay-dp(8)], width=dp(2))
            # ►
            ax,ay = cx+r*0.25+bh*0.5, cy
            Line(points=[ax-dp(8),ay+dp(8),ax+dp(6),ay,ax-dp(8),ay-dp(8)], width=dp(2))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touches[touch.uid] = touch
            self._update_dir(touch)
            return True

    def on_touch_move(self, touch):
        if touch.uid in self._touches:
            self._update_dir(touch)
            return True

    def on_touch_up(self, touch):
        if touch.uid in self._touches:
            del self._touches[touch.uid]
            self.dx = 0; self.dy = 0
            if self.on_move_cb: self.on_move_cb(0,0)
            return True

    def _update_dir(self, touch):
        cx,cy = self.center
        dx = touch.x - cx
        dy = touch.y - cy
        if abs(dx)+abs(dy) < dp(12):
            self.dx=0; self.dy=0
            if self.on_move_cb: self.on_move_cb(0,0)
            return
        if abs(dx) > abs(dy):
            self.dx = 1 if dx>0 else -1; self.dy = 0
        else:
            self.dx = 0; self.dy = 1 if dy>0 else -1
        if self.on_move_cb: self.on_move_cb(self.dx, self.dy)


# ════════════════════════════════════════════════════════════
# ИГРОВОЙ ЭКРАН (карта + движение)
# ════════════════════════════════════════════════════════════
class MapScreen(FloatLayout):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self._dx = 0; self._dy = 0
        self._kai = {'x':0.5,'y':0.5,'dir':'down','frame':0,'tick':0}
        self._idol_cooldown = {}
        self._pillar_shown  = False
        self._dialog_open   = False
        self._tracks        = []
        self._birds         = []
        self._wave_tick     = 0
        self._running       = False
        self._kai_imgs      = {}
        self._load_kai()
        self._build()
        self._loop = None

    # ── Загрузка спрайтов ───────────────────────────────────
    def _load_kai(self):
        try:
            from kivy.core.image import Image as CoreImage
            sheet = CoreImage(res('kai.png'))
            # Спрайтшит 4x4: строки down/left/right/up
            tw,th = sheet.width, sheet.height
            fw,fh = tw//4, th//4
            dirs = ['down','left','right','up']
            for row,d in enumerate(dirs):
                frames = []
                for col in range(4):
                    # Вырезаем регион из текстуры
                    frames.append({'file':res('kai.png'),'row':row,'col':col,'fw':fw,'fh':fh,'tw':tw,'th':th})
                self._kai_imgs[d] = frames
        except Exception as e:
            print('Kai load error:', e)

    # ── Построение UI ───────────────────────────────────────
    def _build(self):
        # Фон карты
        self._map_widget = Image(
            source=res('map.png'),
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(None,None),
        )
        self.add_widget(self._map_widget)

        # Canvas для динамики (идолы, Кай, следы)
        self._dyn = Widget(size_hint=(1,1))
        self.add_widget(self._dyn)

        # HUD сверху
        hud = BoxLayout(
            size_hint=(1,None), height=dp(50),
            pos_hint={'top':1},
            padding=[dp(8),dp(4)], spacing=dp(6)
        )
        with hud.canvas.before:
            Color(*PANEL)
            self._hud_bg = Rectangle(pos=hud.pos, size=hud.size)
        hud.bind(pos=lambda *a: setattr(self._hud_bg,'pos',hud.pos))
        hud.bind(size=lambda *a: setattr(self._hud_bg,'size',hud.size))

        self._parts_lbl = GameLabel(
            text='✈  Запчасти: ○○○○○○○○○',
            font_size=sp(12), size_hint_x=0.7
        )
        hud.add_widget(self._parts_lbl)

        self._score_lbl = GameLabel(text='★ 0', font_size=sp(12), size_hint_x=0.15)
        hud.add_widget(self._score_lbl)

        btn_menu = Button(
            text='☰', font_size=sp(18), size_hint=(None,None),
            size=(dp(44),dp(44)),
            background_normal='', background_color=hex2rgba('#4a2800'),
            color=GOLD2
        )
        btn_menu.bind(on_press=lambda *a: self.app.show_screen('menu'))
        hud.add_widget(btn_menu)

        btn_bag = Button(
            text='🎒', font_size=sp(18), size_hint=(None,None),
            size=(dp(44),dp(44)),
            background_normal='', background_color=hex2rgba('#4a2800'),
            color=GOLD2
        )
        btn_bag.bind(on_press=lambda *a: self.app.show_inventory())
        hud.add_widget(btn_bag)
        self.add_widget(hud)

        # Джойстик — левый нижний угол
        self._joystick = Joystick(
            on_move=self._on_joy,
            pos_hint={'x':0.02,'y':0.02},
        )
        self.add_widget(self._joystick)

    def _on_joy(self, dx, dy):
        self._dx = dx; self._dy = dy

    def start(self, from_save=False):
        self._idol_cooldown = {}
        self._pillar_shown  = False
        self._dialog_open   = False
        self._tracks        = []
        self._birds         = []
        if not from_save:
            self._kai = {'x':0.5,'y':0.5,'dir':'down','frame':0,'tick':0}
        self._running = True
        self._start_time = time.time()
        if self._loop: self._loop.cancel()
        self._loop = Clock.schedule_interval(self._tick, 1/FPS)
        self._update_hud()

    def stop(self):
        self._running = False
        if self._loop:
            self._loop.cancel()
            self._loop = None

    # ── Игровой тик ─────────────────────────────────────────
    def _tick(self, dt):
        if not self._running: return
        self._move()
        self._check_proximity()
        self._anim_kai()
        self._wave_tick += 1
        self._draw()
        # Обновляем счёт
        elapsed = time.time() - self._start_time
        solved  = self.app.game.get('solved',[])
        if len(solved) < 9:
            score = max(0, 9000 - int(elapsed*2) - self.app.hints_used*100)
            self.app.score = score
            self._score_lbl.text = f'★ {score}'

    def _move(self):
        kai = self._kai
        dx,dy = self._dx, self._dy
        if dx==0 and dy==0:
            kai['frame']=0; return
        if dx < 0:   kai['dir']='left'
        elif dx > 0: kai['dir']='right'
        elif dy > 0: kai['dir']='up'
        elif dy < 0: kai['dir']='down'
        spd = KAI_SPEED
        ns  = 0.04
        new_x = max(ns, min(kai['x']+dx*spd, 1.0-ns))
        new_y = max(ns, min(kai['y']+dy*spd, 1.0-ns))
        # Следы
        if kai.get('move_tick',0) % 6 == 0:
            self._tracks.append([kai['x'],kai['y'],0])
        kai['move_tick'] = kai.get('move_tick',0)+1
        self._tracks = [[x,y,a+1] for x,y,a in self._tracks if a<30]
        kai['x'] = new_x; kai['y'] = new_y

    def _anim_kai(self):
        kai = self._kai
        if self._dx!=0 or self._dy!=0:
            kai['tick']+=1
            if kai['tick']>=6: kai['tick']=0; kai['frame']=(kai['frame']+1)%4
        else:
            kai['frame']=0; kai['tick']=0

    def _check_proximity(self):
        if self._dialog_open: return
        kai = self._kai
        solved = self.app.game.get('solved',[])
        for i,(px,py) in enumerate(IDOL_POS):
            dist=math.hypot(kai['x']-px, kai['y']-py)
            if self._idol_cooldown.get(i) and dist>RESET:
                self._idol_cooldown[i]=False
            if self._idol_cooldown.get(i): continue
            if dist < TRIGGER:
                self._idol_cooldown[i]=True
                self._dialog_open=True
                self._show_idol_dialog(i)
                return
        # Столб
        if not self._pillar_shown:
            if math.hypot(kai['x']-0.5, kai['y']-0.45) < 0.055:
                self._pillar_shown=True
                self._show_pillar()

    # ── Отрисовка ───────────────────────────────────────────
    def _map_rect(self):
        w,h = self.width, self.height - dp(50)
        size = min(w,h)
        ox = (w-size)/2; oy = 0
        return ox, oy, size, size

    def _draw(self):
        ox,oy,mw,mh = self._map_rect()
        solved = self.app.game.get('solved',[])
        c = self._dyn.canvas
        c.clear()

        # Следы
        with c:
            for tx,ty,age in self._tracks:
                br = max(0.3, 1.0-age*0.03)
                Color(br*0.7, br*0.55, br*0.3, 0.6)
                sx=ox+tx*mw; sy=oy+ty*mh
                Ellipse(pos=(sx-dp(3),sy-dp(2)),size=(dp(6),dp(4)))

        # Идолы
        with c:
            for i,(px,py) in enumerate(IDOL_POS):
                x=ox+px*mw; y=oy+py*mh
                r=dp(20)
                if i in solved:
                    Color(*hex2rgba('#1a4a00'))
                    Ellipse(pos=(x-r,y-r),size=(r*2,r*2))
                    Color(*GOLD)
                    Ellipse(pos=(x-r,y-r),size=(r*2,r*2))
                else:
                    Color(*hex2rgba('#ff6600'))
                    Line(circle=(x,y,r),width=dp(2.5))
                    Color(*hex2rgba('#ffaa00'))
                    Line(circle=(x,y,r-dp(4)),width=dp(1))

        # Кай
        kai = self._kai
        kx=ox+kai['x']*mw; ky=oy+kai['y']*mh
        s=dp(48)
        with c:
            Color(1,1,1,1)
            Rectangle(
                source=res('kai.png'),
                pos=(kx-s/2, ky-s/2),
                size=(s,s),
                # TODO: spritesheet region — пока весь спрайт
            )

    # ── Диалоги ─────────────────────────────────────────────
    def _show_idol_dialog(self, idx):
        r = RIDDLES[idx]
        solved = self.app.game.get('solved',[])
        already = idx in solved

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(16))
        content.add_widget(GameLabel(
            text=r['name'], font_size=sp(16), bold=True,
            size_hint_y=None, height=dp(36), color=GOLD2
        ))
        msg = '✅ Загадка уже разгадана!' if already else 'Поговорить с этим идолом?'
        content.add_widget(GameLabel(text=msg, halign='center'))
        btns = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10))

        popup = Popup(
            title='', content=content,
            size_hint=(0.85,0.35),
            background='', background_color=hex2rgba('#2a1400'),
            separator_color=GOLD,
        )

        def _close(*a):
            popup.dismiss(); self._dialog_open=False

        def _talk(*a):
            popup.dismiss(); self._dialog_open=False
            if not already:
                self.app.show_riddle(idx)

        if not already:
            b1 = GoldButton(text='💬 Поговорить')
            b1.bind(on_press=_talk); btns.add_widget(b1)
        b2 = GoldButton(text='✖ Мимо')
        b2.background_color = hex2rgba('#3a1a00')
        b2.bind(on_press=_close); btns.add_widget(b2)
        content.add_widget(btns)
        popup.bind(on_dismiss=lambda *a: setattr(self,'_dialog_open',False))
        popup.open()

    def _show_pillar(self):
        msg = (
            'Путник, ты ступил на землю древних.\n\n'
            'Девять духов хранят тайны острова.\n'
            'Реши их все — и самолёт взлетит!\n\n'
            'Есть и десятый дух, скрытый...\nНайди его сам.'
        )
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        content.add_widget(GameLabel(text='📜  Послание столба', font_size=sp(16),
                                     bold=True, color=GOLD2, size_hint_y=None, height=dp(36)))
        content.add_widget(GameLabel(text=msg, halign='center'))
        btn = GoldButton(text='✔  Понял')
        content.add_widget(btn)
        popup = Popup(title='', content=content, size_hint=(0.85,0.5),
                      background='', background_color=hex2rgba('#1a0e00'),
                      separator_color=GOLD)
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def update_hud(self):
        self._update_hud()

    def _update_hud(self):
        solved = self.app.game.get('solved',[])
        icons = ''
        for i in range(9):
            icons += '●' if i in solved else '○'
        self._parts_lbl.text = f'✈  {icons}'


# ════════════════════════════════════════════════════════════
# ЭКРАН ЗАГАДКИ
# ════════════════════════════════════════════════════════════
class RiddleScreen(FloatLayout):
    def __init__(self, app, idx, **kw):
        super().__init__(**kw)
        self.app = app
        self.idx = idx
        self._build()

    def _build(self):
        r = RIDDLES[self.idx]
        # Фон
        bg = Image(source=res(r['img']), allow_stretch=True,
                   keep_ratio=False, size_hint=(1,1))
        self.add_widget(bg)
        with bg.canvas.after:
            Color(0,0,0,0.45)
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=lambda *a: setattr(self._bg_rect,'size',self.size))
        self.bind(pos=lambda *a: setattr(self._bg_rect,'pos',self.pos))

        # Нижняя панель
        panel = BoxLayout(
            orientation='vertical', spacing=dp(8), padding=dp(14),
            size_hint=(1,None), height=dp(260),
            pos_hint={'x':0,'y':0}
        )
        with panel.canvas.before:
            Color(*hex2rgba('#2a1400'))
            self._panel_bg = Rectangle(size=panel.size, pos=panel.pos)
            Color(*GOLD, 1)
            self._panel_line = Line(rectangle=(0,0,0,0), width=dp(2))
        panel.bind(pos=self._update_panel_bg, size=self._update_panel_bg)

        # Заголовок + кнопка назад
        hdr = BoxLayout(size_hint_y=None, height=dp(40))
        hdr.add_widget(GameLabel(text=r['name'], font_size=sp(13), bold=True,
                                  color=GOLD2))
        btn_back = Button(text='◀ Карта', font_size=sp(13),
                          size_hint=(None,1), width=dp(90),
                          background_normal='', background_color=hex2rgba('#4a2800'),
                          color=GOLD2)
        btn_back.bind(on_press=lambda *a: self.app.show_screen('map'))
        hdr.add_widget(btn_back)
        panel.add_widget(hdr)

        # Текст загадки
        panel.add_widget(GameLabel(
            text=r['text'], halign='center', font_size=sp(14),
            bold=True, size_hint_y=None, height=dp(90),
        ))

        # Подсказка
        self._hint_lbl = GameLabel(text='', font_size=sp(12),
                                    color=hex2rgba('#ffcc44'),
                                    size_hint_y=None, height=dp(24))
        panel.add_widget(self._hint_lbl)

        # Поле ввода + кнопки
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        row.add_widget(GameLabel(text='Ответ:', font_size=sp(13),
                                  size_hint_x=None, width=dp(60)))
        self._entry = TextInput(
            hint_text='Введи ответ...', multiline=False,
            font_size=sp(14), size_hint_x=0.5,
            background_color=hex2rgba('#3d1e00'),
            foreground_color=hex2rgba('#f5e6c8'),
            cursor_color=GOLD2,
        )
        self._entry.bind(on_text_validate=lambda *a: self._check())
        row.add_widget(self._entry)

        btn_ok = GoldButton(text='✔ Готово', size_hint_x=None, width=dp(100))
        btn_ok.bind(on_press=lambda *a: self._check())
        row.add_widget(btn_ok)

        btn_hint = Button(text='💡', font_size=sp(18),
                          size_hint=(None,None), size=(dp(50),dp(50)),
                          background_normal='', background_color=hex2rgba('#4a2800'),
                          color=GOLD2)
        btn_hint.bind(on_press=lambda *a: self._show_hint())
        row.add_widget(btn_hint)
        panel.add_widget(row)

        # Результат
        self._result_lbl = GameLabel(text='', font_size=sp(13),
                                      size_hint_y=None, height=dp(28))
        panel.add_widget(self._result_lbl)
        self.add_widget(panel)

    def _update_panel_bg(self, w, *a):
        self._panel_bg.pos  = w.pos
        self._panel_bg.size = w.size
        self._panel_line.rectangle = (*w.pos, *w.size)

    def _check(self):
        r = RIDDLES[self.idx]
        ans = self._entry.text.strip().lower()
        if ans == r['answer'].lower():
            self._result_lbl.text  = f'✅  Верно! {r["part_name"]} — в рюкзак!'
            self._result_lbl.color = (0.3,0.9,0.3,1)
            solved = self.app.game.setdefault('solved',[])
            if self.idx not in solved:
                solved.append(self.idx)
            self.app.save_progress()
            self.app.map_screen.update_hud()
            Clock.schedule_once(lambda *a: self._show_part_received(), 0.4)
        else:
            self._result_lbl.text  = '❌  Неверно. Попробуй ещё!'
            self._result_lbl.color = hex2rgba('#cc3300')
            self._entry.text = ''

    def _show_hint(self):
        r = RIDDLES[self.idx]
        if self.app.settings.get('hints',True):
            self._hint_lbl.text = f'💡 {r["hint"]}'
            self.app.hints_used += 1
        else:
            self._hint_lbl.text = 'Подсказки отключены в настройках'

    def _show_part_received(self):
        r = RIDDLES[self.idx]
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(16))
        content.add_widget(Image(source=res(r['part_icon']),
                                  size_hint_y=None, height=dp(120),
                                  allow_stretch=True, keep_ratio=True))
        content.add_widget(GameLabel(text=f'🎉 {r["part_name"]}', font_size=sp(18),
                                      bold=True, color=GOLD2, halign='center'))
        content.add_widget(GameLabel(text=f'{r["name"]}\nдарит тебе эту запчасть!',
                                      halign='center'))
        btn = GoldButton(text='✔ Отлично! В рюкзак')
        content.add_widget(btn)
        popup = Popup(title='', content=content, size_hint=(0.85,0.55),
                      background='', background_color=hex2rgba('#1a0e00'),
                      separator_color=GOLD)
        def _done(*a):
            popup.dismiss()
            self.app.show_screen('map')
            if len(self.app.game.get('solved',[])) == 9:
                Clock.schedule_once(lambda *a: self.app.show_victory(), 0.3)
        btn.bind(on_press=_done)
        popup.open()


# ════════════════════════════════════════════════════════════
# ЭКРАН ЗАСТАВКИ
# ════════════════════════════════════════════════════════════
class SplashScreen(FloatLayout):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        bg = Image(source=res('splash.png'), allow_stretch=True,
                   keep_ratio=False, size_hint=(1,1))
        self.add_widget(bg)

        btn = GoldButton(
            text='▶  НАЧАТЬ ПРИКЛЮЧЕНИЕ',
            size_hint=(0.7,None), height=dp(64),
            pos_hint={'center_x':0.5,'y':0.06},
            font_size=sp(18)
        )
        btn.bind(on_press=lambda *a: app.show_screen('menu'))
        self.add_widget(btn)


# ════════════════════════════════════════════════════════════
# ГЛАВНОЕ МЕНЮ
# ════════════════════════════════════════════════════════════
class MenuScreen(FloatLayout):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        bg = Image(source=res('splash.png'), allow_stretch=True,
                   keep_ratio=False, size_hint=(1,1))
        self.add_widget(bg)
        with self.canvas.after:
            Color(0,0,0,0.55)
            self._ov = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=lambda *a: setattr(self._ov,'size',self.size))
        self.bind(pos=lambda *a: setattr(self._ov,'pos',self.pos))

        panel = BoxLayout(
            orientation='vertical', spacing=dp(10), padding=dp(20),
            size_hint=(0.7,None), height=dp(440),
            pos_hint={'x':0.05,'center_y':0.5}
        )
        with panel.canvas.before:
            Color(*hex2rgba('#1a0900'), 1)
            self._pb = Rectangle()
        panel.bind(pos=lambda w,v: setattr(self._pb,'pos',v))
        panel.bind(size=lambda w,v: setattr(self._pb,'size',v))

        panel.add_widget(GameLabel(text='🏝  ISLAND\nADVENTURES',
                                    font_size=sp(26), bold=True, color=GOLD2,
                                    halign='left', size_hint_y=None, height=dp(80)))
        panel.add_widget(Widget(size_hint_y=None, height=dp(2)))

        items = [
            ('🗺  НОВАЯ ИГРА',  lambda *a: app.new_game()),
            ('📂  ЗАГРУЗИТЬ',   lambda *a: app.load_screen()),
            ('💾  СОХРАНИТЬ',   lambda *a: app.save_screen()),
            ('🎵  МУЗЫКА',      lambda *a: app.music_screen()),
            ('📖  ОТ АВТОРА',   lambda *a: app.about_screen()),
            ('🚪  ВЫХОД',       lambda *a: App.get_running_app().stop()),
        ]
        for text, cb in items:
            b = GoldButton(text=text, font_size=sp(15))
            b.bind(on_press=cb)
            panel.add_widget(b)
        self.add_widget(panel)


# ════════════════════════════════════════════════════════════
# РЮКЗАК (инвентарь)
# ════════════════════════════════════════════════════════════
class InventoryScreen(FloatLayout):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(*hex2rgba('#120900'))
            Rectangle(size=self.size, pos=self.pos)

        # Заголовок
        hdr = BoxLayout(size_hint=(1,None), height=dp(56), padding=dp(8))
        with hdr.canvas.before:
            Color(*hex2rgba('#3d1e00'))
            Rectangle(size=hdr.size, pos=hdr.pos)
        hdr.bind(size=lambda w,v: None)
        hdr.add_widget(GameLabel(text='🎒  РЮКЗАК КАЯ', font_size=sp(18),
                                  bold=True, color=GOLD2))
        btn_back = GoldButton(text='◀ На карту', size_hint_x=None, width=dp(120))
        btn_back.bind(on_press=lambda *a: self.app.show_screen('map'))
        hdr.add_widget(btn_back)
        self.add_widget(hdr)

        # Сетка 3x3
        from kivy.uix.gridlayout import GridLayout
        grid = GridLayout(
            cols=3, spacing=dp(10), padding=dp(10),
            size_hint=(1,None),
            pos_hint={'x':0,'top':0.88}
        )
        self._slots = []
        for i in range(9):
            slot = BoxLayout(orientation='vertical', spacing=dp(4),
                             size_hint_y=None, height=dp(140))
            with slot.canvas.before:
                Color(*hex2rgba('#3a2010'))
                self._slot_bg = RoundedRectangle(
                    size=slot.size, pos=slot.pos, radius=[dp(8)])
            img = Image(allow_stretch=True, keep_ratio=True,
                        size_hint_y=0.75)
            lbl = GameLabel(text='', font_size=sp(10), halign='center',
                             size_hint_y=0.25)
            slot.add_widget(img)
            slot.add_widget(lbl)
            grid.add_widget(slot)
            self._slots.append((slot,img,lbl))
        self.add_widget(grid)

        # Прогресс
        self._prog = GameLabel(
            text='Запчастей: 0 / 9', font_size=sp(14), color=GOLD,
            size_hint=(1,None), height=dp(36),
            pos_hint={'x':0,'y':0.02}
        )
        self.add_widget(self._prog)

    def refresh(self):
        solved = self.app.game.get('solved',[])
        for i,(slot,img,lbl) in enumerate(self._slots):
            r = RIDDLES[i]
            if i in solved:
                img.source = res(r['part_icon'])
                lbl.text   = r['part_name']
                lbl.color  = GOLD2
            else:
                img.source = ''
                lbl.text   = f'#{i+1}'
                lbl.color  = DIM
        n = len(solved)
        self._prog.text = f'Запчастей: {n} / 9  {"✈ Готово!" if n==9 else ""}'


# ════════════════════════════════════════════════════════════
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ════════════════════════════════════════════════════════════
class IslandAdventuresApp(App):
    def build(self):
        self.title  = 'Island Adventures'
        self.icon   = res('icon.png')
        self.settings = load_settings()
        self.game   = {'solved':[]}
        self.score  = 0
        self.hints_used = 0
        self._music = None
        self._screens = {}
        self.root_widget = FloatLayout()

        # Строим экраны
        self.splash_screen    = SplashScreen(self)
        self.menu_screen      = MenuScreen(self)
        self.map_screen       = MapScreen(self)
        self.inventory_screen = InventoryScreen(self)

        self._screens = {
            'splash': self.splash_screen,
            'menu':   self.menu_screen,
            'map':    self.map_screen,
            'inv':    self.inventory_screen,
        }
        for s in self._screens.values():
            self.root_widget.add_widget(s)

        self.show_screen('splash')

        if self.settings.get('music',True):
            Clock.schedule_once(lambda *a: self._play_music('music.mp3'), 0.5)

        return self.root_widget

    # ── Экраны ──────────────────────────────────────────────
    def show_screen(self, name):
        for s in self._screens.values(): s.opacity=0; s.disabled=True
        if name in self._screens:
            self._screens[name].opacity=1
            self._screens[name].disabled=False
        self._current = name
        # Музыка
        if name=='map' and self.settings.get('music',True):
            self._play_music('music_game.mp3')
        elif name in ('splash','menu') and self.settings.get('music',True):
            self._play_music('music.mp3')

    def show_inventory(self):
        self.inventory_screen.refresh()
        self.show_screen('inv')

    def show_riddle(self, idx):
        key = f'riddle_{idx}'
        if key not in self._screens:
            rs = RiddleScreen(self, idx)
            self._screens[key] = rs
            self.root_widget.add_widget(rs)
        self.show_screen(key)

    # ── Музыка ──────────────────────────────────────────────
    def _play_music(self, fname):
        if self._music:
            try: self._music.stop()
            except: pass
        try:
            self._music = SoundLoader.load(res(fname))
            if self._music:
                self._music.volume = self.settings.get('volume',0.6)
                self._music.loop   = True
                self._music.play()
        except Exception as e:
            print('Music error:', e)

    # ── Игра ────────────────────────────────────────────────
    def new_game(self):
        self.game = {'solved':[]}
        self.score = 0
        self.hints_used = 0
        self.show_screen('map')
        self.map_screen.start()

    def save_progress(self):
        pass  # автосохранение при решении загадки

    def load_screen(self):
        self._show_slots_popup('load')

    def save_screen(self):
        self._show_slots_popup('save')

    def _show_slots_popup(self, mode):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(16))
        title = '💾 Сохранить' if mode=='save' else '📂 Загрузить'
        content.add_widget(GameLabel(text=title, font_size=sp(18), bold=True,
                                      color=GOLD2, size_hint_y=None, height=dp(40)))
        popup = Popup(title='', content=content, size_hint=(0.85,0.55),
                      background='', background_color=hex2rgba('#1a0e00'),
                      separator_color=GOLD)
        for n in [1,2]:
            data = load_slot(n)
            slot_lbl = data['slot_name'] if data else 'Пусто'
            cnt = data['solved_count'] if data else 0
            txt = f'Слот {n}: {slot_lbl}' + (f'  ({cnt}/9)' if data else '')
            b = GoldButton(text=txt, font_size=sp(13))
            if mode=='save':
                def _save(nn=n, *a):
                    save_slot(nn, dict(self.game))
                    popup.dismiss()
                b.bind(on_press=_save)
            else:
                def _load(nn=n, *a):
                    d = load_slot(nn)
                    if d:
                        self.game = d
                        self.show_screen('map')
                        self.map_screen.start(from_save=True)
                    popup.dismiss()
                b.bind(on_press=_load)
            content.add_widget(b)
        content.add_widget(GoldButton(text='Отмена', font_size=sp(13),
                                       background_color=hex2rgba('#3a1a00'))
                           ).bind if False else None
        btn_cancel = GoldButton(text='Отмена', font_size=sp(13))
        btn_cancel.background_color = hex2rgba('#3a1a00')
        btn_cancel.bind(on_press=popup.dismiss)
        content.add_widget(btn_cancel)
        popup.open()

    def music_screen(self):
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))
        content.add_widget(GameLabel(text='🎵 Музыка', font_size=sp(18), bold=True,
                                      color=GOLD2, size_hint_y=None, height=dp(40)))
        # Слайдер громкости
        content.add_widget(GameLabel(text='Громкость:', size_hint_y=None, height=dp(30)))
        sl = Slider(min=0, max=1, value=self.settings.get('volume',0.6),
                    size_hint_y=None, height=dp(44))
        def _vol(w,v):
            self.settings['volume']=v
            if self._music: self._music.volume=v
            save_settings(self.settings)
        sl.bind(value=_vol)
        content.add_widget(sl)
        # Вкл/Выкл
        is_on = self.settings.get('music',True)
        btn_tog = GoldButton(text='🔇 Выключить' if is_on else '🔊 Включить',
                              size_hint_y=None, height=dp(52))
        def _tog(*a):
            on = not self.settings.get('music',True)
            self.settings['music']=on
            save_settings(self.settings)
            if on: self._play_music('music_game.mp3' if self._current=='map' else 'music.mp3')
            else:
                if self._music: self._music.stop()
            btn_tog.text = '🔇 Выключить' if on else '🔊 Включить'
        btn_tog.bind(on_press=_tog)
        content.add_widget(btn_tog)
        popup = Popup(title='', content=content, size_hint=(0.8,0.5),
                      background='', background_color=hex2rgba('#1a0e00'),
                      separator_color=GOLD)
        content.add_widget(GoldButton(text='Закрыть').bind if False else
                           self._close_btn(popup, content))
        popup.open()

    def _close_btn(self, popup, parent):
        b = GoldButton(text='Закрыть', size_hint_y=None, height=dp(52))
        b.bind(on_press=popup.dismiss)
        parent.add_widget(b)

    def about_screen(self):
        msg = (
            'Добро пожаловать в Island Adventures!\n\n'
            'После крушения самолёта предстоит\n'
            'собрать запчасти, решив 9 загадок.\n\n'
            'Желаю удачи и приятного приключения!\n\n'
            'Автор игры — ToxtroN'
        )
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        content.add_widget(GameLabel(text='📖 От автора', font_size=sp(18), bold=True,
                                      color=GOLD2, size_hint_y=None, height=dp(40)))
        content.add_widget(GameLabel(text=msg, halign='center'))
        btn = GoldButton(text='◀ В меню')
        popup = Popup(title='', content=content, size_hint=(0.85,0.65),
                      background='', background_color=hex2rgba('#1a0e00'),
                      separator_color=GOLD)
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def show_victory(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        content.add_widget(GameLabel(text='🎉 ПОЗДРАВЛЯЕМ!', font_size=sp(22), bold=True,
                                      color=GOLD2, halign='center', size_hint_y=None, height=dp(50)))
        content.add_widget(GameLabel(
            text='Кай решил все 9 загадок!\nВсе запчасти собраны.\nСамолёт готов взлетать! ✈',
            halign='center', font_size=sp(15)
        ))
        btns = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10))
        b1 = GoldButton(text='🔄 Снова')
        b2 = GoldButton(text='🚪 Выход')
        b1.background_color = hex2rgba('#1a4a00')
        b2.background_color = hex2rgba('#4a1a00')
        popup = Popup(title='', content=content, size_hint=(0.85,0.55),
                      background='', background_color=hex2rgba('#0a0e00'),
                      separator_color=GOLD)
        b1.bind(on_press=lambda *a: (popup.dismiss(), self.new_game()))
        b2.bind(on_press=lambda *a: App.get_running_app().stop())
        btns.add_widget(b1); btns.add_widget(b2)
        content.add_widget(btns)
        popup.open()


if __name__ == '__main__':
    IslandAdventuresApp().run()
