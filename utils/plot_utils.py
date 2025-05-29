import matplotlib.pyplot as plt


def export_legend(legend, filename="legend.pdf"):
	fig = legend.figure
	fig.canvas.draw()
	bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
	fig.savefig(filename, dpi=300, bbox_inches=bbox)
	plt.close()


def make_legend(outpath, labels, markers=None, colors=None,
				markeredgecolors=None, linestyles=None):

	# put properties into dict with defaults
	p = {
		'm': ['o'] * len(labels),
		'c': ['k'] * len(labels),
		'mec': [None] * len(labels),
		'ls': ['solid'] * len(labels)}

	# update properties with user input
	for inp, (property, default) in zip(
		[markers, colors, markeredgecolors, linestyles],
		p.items()):
		if inp is not None:
			if type(inp) is str:  # if single item, repeat for each label
				inp = [inp] * len(labels)
			p[property] = inp

	# make legend
	handles = [
		plt.plot([], [], marker=m, c=c, mec=mec, ls=ls)[0] for
		m, c, mec, ls in zip(p['m'], p['c'], p['mec'], p['ls'])]
	legend = plt.legend(handles, labels, loc=3)
	export_legend(legend, filename=outpath)
	plt.close()


custom_defaults = {
	'font.size': 10,
	'lines.linewidth': 1,
	'lines.markeredgewidth': 1,
	'lines.markersize': 6,
	'savefig.dpi': 300,
	'legend.frameon': False,
	'ytick.direction': 'in',
	'ytick.major.width': .8,
	'xtick.direction': 'in',
	'xtick.major.width': .8,
	'axes.spines.top': False,
	'axes.spines.right': False,
	'axes.linewidth': .8}

distinct_colors_255 = {
	'red': (230, 25, 75),
	'green': (60, 180, 75),
	'yellow': (255, 225, 25),
	'blue': (0, 130, 200),
	'orange': (245, 130, 48),
	'purple': (145, 30, 180),
	'cyan': (70, 240, 240),
	'magenta': (240, 50, 230),
	'lime': (210, 245, 60),
	'pink': (250, 190, 212),
	'teal': (0, 128, 128),
	'lavender': (220, 190, 255),
	'brown': (170, 110, 40),
	'beige': (255, 250, 200),
	'maroon': (128, 0, 0),
	'mint': (170, 255, 195),
	'olive': (128, 128, 0),
	'apricot': (255, 215, 180),
	'navy': (0, 0, 128),
	'white': (255, 255, 255),
	'black': (0, 0, 0),
	'gray': (127, 127, 127)}


distinct_colors = {k: tuple([x / 255. for x in v])
				   for k, v in distinct_colors_255.items()}
