
from sgfmill import sgf as Sgf
from sgfmill import sgf_properties as Sgf_properties

from board import Board

class Metadata:
  def __init__(self, size, bname, wname, brank, wrank, komi):
    self.size = size
    self.bname = bname
    self.wname = wname
    self.brank = brank
    self.wrank = wrank
    self.komi = komi

#Returns (metadata, list of setup stones, list of move stones)
#Setup and move stones are both pairs of (pla,loc)
def load_sgf_moves_exn(path):
  sgf_file = open(path,"rb")
  contents = sgf_file.read()
  sgf_file.close()

  game = Sgf.Sgf_game.from_bytes(contents)
  size = game.get_size()

  root = game.get_root()
  ab, aw, ae = root.get_setup_stones()
  setup = []
  if ab or aw:
    for (row,col) in ab:
      loc = Board.loc_static(col,size-1-row,size)
      setup.append((Board.BLACK,loc))
    for (row,col) in aw:
      loc = Board.loc_static(col,size-1-row,size)
      setup.append((Board.WHITE,loc))

    color,raw = root.get_raw_move()
    if color is not None:
      raise Exception("Found both setup stones and normal moves in root node")

  #Walk down the leftmost branch and assume that this is the game
  moves = []
  prev_pla = None
  seen_white_moves = False
  node = root
  while node:
    node = node[0]
    if node.has_setup_stones():
      raise Exception("Found setup stones after the root node")

    color,raw = node.get_raw_move()
    if color is None:
      raise Exception("Found node without move color")

    if color == 'b':
      pla = Board.BLACK
    elif color == 'w':
      pla = Board.WHITE
    else:
      raise Exception("Invalid move color: " + color)

    rc = Sgf_properties.interpret_go_point(raw, size)
    if rc is None:
      loc = None
    else:
      (row,col) = rc
      loc = Board.loc_static(col,size-1-row,size)

    #Forbid consecutive moves by the same player, unless the previous player was black and we've seen no white moves yet (handicap setup)
    if pla == prev_pla and not (prev_pla == Board.BLACK and not seen_white_moves):
      raise Exception("Multiple moves in a row by same player")
    moves.append((pla,loc))

    prev_pla = pla
    if pla == Board.WHITE:
      seen_white_moves = True

  #If there are multiple black moves in a row at the start, assume they are more handicap stones
  first_white_move_idx = 0
  while first_white_move_idx < len(moves) and moves[first_white_move_idx][0] == Board.BLACK:
    first_white_move_idx += 1
  if first_white_move_idx >= 2:
    setup.extend((pla,loc) for (pla,loc) in moves[:first_white_move_idx] if loc is not None)
    moves = moves[first_white_move_idx:]

  bname = root.get("PB")
  wname = root.get("PW")
  brank = (root.get("BR") if root.has_property("BR") else None)
  wrank = (root.get("WR") if root.has_property("WR") else None)
  komi = (root.get("KM") if root.has_property("KM") else None)

  metadata = Metadata(size, bname, wname, brank, wrank, komi)
  return metadata, setup, moves
