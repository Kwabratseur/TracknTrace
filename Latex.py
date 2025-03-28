import matplotlib.pyplot as plt

import inspect
from pytexit import py2tex
import io
from PIL import Image, ImageChops

white = (255, 255, 255, 255)

def latex_to_img(tex):
    buf = io.BytesIO()
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.axis('off')
    plt.text(0.05, 0.5, f'${tex}$', size=40)
    plt.savefig(buf, format='png')
    plt.close()

    im = Image.open(buf)
    bg = Image.new(im.mode, im.size, white)
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    return im.crop(bbox)

def Lambda2Tex(lmd, VERBOSE=0):
    f = inspect.getsourcelines(lmd)[0][0].split(":")
    eq = f[0].split('"')[1]
    if VERBOSE > 0:
        print(eq)
    fcn = f[-1].split(",")[0].split("}")[0]
    if VERBOSE > 1:
        print(fcn)
    eq = eq + " =" + fcn
    if VERBOSE > 2:
        print(eq)
    return eq

lambdaDict = {"Qtr": lambda Tamb, Tavg, U: (Tamb-Tavg)*0.001/ U,
              "Qhi": lambda HeatInput: HeatInput,
              "Qsol": lambda P_sun, Ag, Ga: P_sun*Ag*Ga,
              "dTobj": lambda Qsol, Qhi, Qtr, dt, C: (Qtr+Qhi+Qsol)*dt/C,
              "Tavg": lambda Tavg, dTobj: Tavg + dTobj}

for i in lambdaDict:
    tex = Lambda2Tex(lambdaDict[i])
    test = py2tex(tex,print_formula=False, print_latex=False, output="tex").replace("$","")
    latex_to_img(test).save('{}.png'.format(i))
    # turn of prints of py2tex, use ipython display and Latex to render latex eq
