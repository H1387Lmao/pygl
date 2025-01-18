import sys, os
from pygame.event import Event
import win32gui
import win32con
from functools import reduce

sys.stdout = open(os.devnull, 'w')
import pygame
sys.stdout = sys.__stdout__

def _parse_size(size) -> list[int]:
	if isinstance(size, (tuple, set, list)):
		if len(size)!=2: raise Error("Size: Invalid width and height.")
		return list(size)
	elif isinstance(size, str):
		try:
			if len(size.split('x'))!=2: raise Error("Size: Invalid width and height.")
			return [int(i) for i in size.split('x')]
		except TypeError:
			raise Error("Size: Invalid width and height")
	else:
		raise Error("Size: Can only parse size with these types: (Tuple, Str, List, Set)")

class WindowStyle:
	NOFRAME = 32
	RESIZABLE = 16
	SHOWN = 64
	HIDDEN = 128
	MAXIMIZED = 1
	FULLSCREEN = -2147483648
	OPENGL = 2
	SCALED = 512
	NOTRESCALABLE = 4
class EventTypes:
	KeyDown = 768
	KeyUp = 769
	KeyHeld=69
class KeyState:
	def __init__(self, char):
		self.char = char
	def __repr__(self):
		return self.char
	def __eq__(self, other):
		return self.char == other
evs = {v:str(e) for e, v in EventTypes.__dict__.items() if not e.startswith('__')}

class Error(Exception):
	def __init__(self, m):
		super().__init__(m)
class Background:
	def __init__(self, color="#FFFFFF"):
		self.clr = color
class States:
	def __init__(self, **kwargs):
		self.states={}
		self.states.update(kwargs)
	def __getitem__(self, index):
		return self.states[index]
	def __setitem__(self, index, value):
		self.states[index]=value
	def default(self):
		self.states['running']=True
class Square:
	def __init__(self, pos, size, color="#FFFF00"):
		self.size:list[int]=_parse_size(size)
		self.pos:list[int] =_parse_size(pos)
		self.BG = color
	def draw(self, screen_surface):
		self.rect = pygame.rect.Rect(*self.pos, *self.size)
		pygame.draw.rect(screen_surface, self.BG, self.rect)
class Sprite:
	def __init__(self, sprite_path, pos, size, crop=False):
		self.size:list[int]=_parse_size(size)
		self.pos:list[int] =_parse_size(pos)
		if os.path.isfile(sprite_path):
			self.image = pygame.image.load(sprite_path)
			if crop:
				raise NotImplemented("Cannot crop images yet")
			self.image = pygame.transform.scale(self.image, self.size)
		else:
			raise Exception("Image: Invalid image file.")
	def draw(self, screen_surface : pygame.Surface):
		rect = pygame.rect.Rect(*self.pos,*self.size)
		screen_surface.blit(self.image, rect)
class Window:
	def remove_min_max_buttons(self, hwnd):
		style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
		
		style &= ~win32con.WS_MINIMIZEBOX
		style &= ~win32con.WS_MAXIMIZEBOX

		win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

		win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
	def __init__(self, size=(300,300), title='Pygl Window', styles=[]):
		for i,v in EventTypes.__dict__.items():
			if i.startswith('__'):
				continue
			setattr(self, i, v)
		styles = reduce(lambda x, y: x | y, styles, 0)
		self.width, self.height = _parse_size(size)
		self.title=title
		
		self.screen_surface=pygame.display.set_mode((self.width, self.height), styles)
		if styles&WindowStyle.NOTRESCALABLE:
			styles^=WindowStyle.NOTRESCALABLE
			self.remove_min_max_buttons(pygame.display.get_wm_info()['window'])
		if styles%2!=0:
			styles^=0b1
			pygame.display.iconify()
			self.maximize()
		pygame.init()
		self.states=States(
			styles=styles,
		)
		self.background=Background()
		self.objs=[]
	def add_object(self, object):
		self.objs.append(object)
	def display_all_objects(self):
		for obj in self.objs:
			obj.draw(self.screen_surface)
	def maximize(self):
		self.hwnd=pygame.display.get_wm_info()['window']
		win32gui.ShowWindow(self.hwnd, win32con.SW_MAXIMIZE)
	def __update_loop(self):
		self.screen_surface.fill(self.background.clr)
		self.display_all_objects()
		pygame.display.update()
	def add_listener(self, event_type, function):
		setattr(self, evs[event_type], function)
	def event_is_init(self, event_type):
		try:
			res = getattr(self, evs[event_type])
		except KeyError:
			return 0
		if res:
			return res 
		else:
			return 0
	def get_requirements(self, func):
		requirements={}
		for param_name, param in func.__annotations__.items():
			requirements[param_name] = param
		return requirements
	def acquire(self, args):
		if args==KeyState:
			return KeyState(self.recent_key)
	def __get_pressed(self):
		pressed = pygame.key.get_pressed()
		pressed_keys_list = [pygame.key.name(i) for i in range(len(pressed)) if pressed[i]]
		return pressed_keys_list
	def run(self):
		pygame.display.set_caption(self.title)
		self.clock = pygame.time.Clock()

		self.states.default()

		while self.states['running']:
			if self.KeyHeld != 69:# pyright: ignore
				pressed = self.__get_pressed()
				if pressed:
					for key in pressed:
						self.KeyHeld(KeyState(key))# pyright: ignore
			for event in pygame.event.get():
				if event.type == EventTypes.KeyDown:
					self.recent_key=event.dict['unicode']
				res=self.event_is_init(event.type)
				if not isinstance(res, int):
					reqs=self.get_requirements(res)
					args=[]
					for _, argument in reqs.items():
						args.append(self.acquire(argument))
					res(*args)
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
			self.__update_loop()


window = Window(size="600x600", styles=[WindowStyle.RESIZABLE, WindowStyle.NOTRESCALABLE])
sprite = Sprite("enemy.png", "10x10", "50x50")

def handle_key_input(key: KeyState):
    movement = {
        "d": (1, 0),
        "a": (-1, 0),
        "w": (0, -1),
        "s": (0, 1),
    }
    if key.char in movement:
        dx, dy = movement[key.char]
        sprite.pos[0] += dx
        sprite.pos[1] += dy

window.add_listener(EventTypes.KeyHeld, handle_key_input)
window.add_object(sprite)
window.run()
