import png
import StringIO

W = 100
H = 100

buff = StringIO.StringIO()
writer = png.Writer(size=(W,H), bitdepth=4)
lines = [
    [0,0,0] * H
    for x in range(W)
]

def draw1(off_x, off_y, width, heigh, color):
  dx = float(width) / heigh

  wx = off_x

  for y in range(off_y, off_y+heigh):
    _wx2 = int(wx)
    for x in range(off_x, _wx2):
        lines[y][x*3+0] = color[0]
        lines[y][x*3+1] = color[1]
        lines[y][x*3+2] = color[2]

    wx += dx

def draw2(off_x, off_y, width, heigh, color):
  dx = float(width) / heigh

  wx = width + off_x

  for y in range(off_y, off_y+heigh):
    _wx2 = int(wx)
    for x in range(off_x, _wx2):
        lines[y][x*3+0] = color[0]
        lines[y][x*3+1] = color[1]
        lines[y][x*3+2] = color[2]

    wx -= dx

def draw3(off_x, off_y, width, heigh, color):
  dx = float(width) / heigh

  wx = off_x

  for y in range(off_y, off_y+heigh):
    _wx2 = int(wx)
    for x in range(off_x, _wx2):
        x = off_x + width + x - _wx2
        lines[y][x*3+0] = color[0]
        lines[y][x*3+1] = color[1]
        lines[y][x*3+2] = color[2]

    wx += dx

def draw4(off_x, off_y, width, heigh, color):
  dx = float(width) / heigh

  wx = width + off_x

  for y in range(off_y, off_y+heigh):
    _wx2 = int(wx)
    for x in range(off_x, _wx2):
        x = off_x + width + x - _wx2
        lines[y][x*3+0] = color[0]
        lines[y][x*3+1] = color[1]
        lines[y][x*3+2] = color[2]

    wx -= dx



def rb(colors):
    draw1(off_x=0, off_y=00, width=50, heigh=50, color=colors[1])
    draw2(off_x=0, off_y=50, width=50, heigh=50, color=colors[1])
    draw3(off_x=0, off_y=50, width=50, heigh=50, color=colors[4])

    draw1(off_x=50, off_y=50, width=50, heigh=50, color=colors[2])
    draw3(off_x=50, off_y=0, width=50, heigh=50, color=colors[3])
    draw4(off_x=50, off_y=50, width=50, heigh=50, color=colors[3])

    draw2(off_x=50, off_y=0, width=50, heigh=50, color=colors[0])

    draw4(off_x=0, off_y=00, width=50, heigh=50, color=colors[5])


    return lines

def data(lines):
  img = png.from_array(lines, 'RGB')

  buff.seek(0)
  writer.write(buff, img.rows)

  return buff.getvalue()
