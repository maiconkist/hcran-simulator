from antenna import *
from user import *
from grid import *

def basic_moving_strategy( pos ):
	# moves only to the left
	if pos[0] < 1000:
		return [ pos[0]+1, pos[1] ]
	else:
		return pos


def build_simulation(n_user, n_rrh):
	grid = Grid(size = (0, 1000) )

	for u in range(n_user):
		grid.add_user(
			User(
				pos= grid.random_pos(),
				moving_strategy= basic_moving_strategy,
				grid = grid
			)
		)
	for r in range(n_rrh):
		grid.add_antenna(
			Antenna(
				pos= grid.random_pos(),
				radius = 100,
				grid = grid,
			)
		)

	return grid

if __name__ == '__main__':


	grid = build_simulation(10, 500)


	# simulate for 600 seconds, 1 second step
	for step in range(600):
		print("-- Simulating step %d/%d" % (step, 600) )
		grid.step( 1 )
