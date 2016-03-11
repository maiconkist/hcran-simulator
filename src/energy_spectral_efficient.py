from ra_greedy import *
from antenna import *
from user import *
from bbu import *
from controller import *
from util import *
from grid import *
import csv
import random

TOTAL_BBU  = [2]
TOTAL_BS  = [1]                #quantidade de macro cells
TOTAL_RRH = [305, 310, 315, 320, 325, 330, 335, 340, 345, 350, 355, 360, 365, 370, 375, 380, 385, 390, 395, 400, 405, 410, 415, 420, 425, 430, 435, 440, 445, 450, 455, 460, 465, 470, 475, 480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535, 540, 545, 550, 555, 560, 565, 570, 575, 580, 585, 590, 595, 600]               #quantidade de femto cells
TOTAL_UE  = [200]			#quantidade de usuarios
REPETICOES = 1000
#COLETAS  = 1

#MARSHOUD_CENARY = 1
#LEONHART_CENARY = 2

#quantidade de usuarios inserida a cada iteracao
#ITERATIONS_UE = {1:1, 5:1, 10:2, 50:5, 100:10, 500:20, 1000:30, 5000:40, 10000:50}

# define posicao de BSs, RRHs e UEs no cenario, bem como seu tipo
def build_scenario(n_bbu, total_bs, total_rrhs, total_ues ):
    #random.seed()
    # Instantiation order. Must be respected
    # 1- Grid
    # 2- Controller
    # 3- BBUs
    # 4- Antennas
    # 5- Users

    grid = Grid(size=(1000, 1000))

    cntrl = Controller(grid, control_network=False)
    grid.add_controller(cntrl)

    for b in range(n_bbu):
        grid.add_bbu(
            BBU(pos=grid.random_pos(), controller=cntrl, grid=grid)
        )
    
    for i in range( total_bs ):
        #insert bs
        bs = Antenna( 0, Antenna.BS_ID, ( grid.size[0]/2, grid.size[1]/2 ), None, grid )
        grid.add_antenna( bs )
        
    #insert rrh
    for j in range( total_rrhs ):
        #if j == 0:
        #    pos_x = 670
        #    pos_y = 400
        #else:
        #    pos_x = 700
        #    pos_y = 400
        pos_x = random.randint( 0, grid.size[0] - 1 )
        pos_y = random.randint( 0, grid.size[1] - 1 )
            
        while grid.add_antenna( Antenna( j+1, Antenna.RRH_ID, ( pos_x, pos_y ), None, grid ) ) == 0:
            pos_x = random.randint( 0, grid.size[0] - 1 )
            pos_y = random.randint( 0, grid.size[1] - 1 )
                
    #insert ue
    for j in range( total_ues ):
        pos_x = random.randint( 0, grid.size[0] - 1 )
        pos_y = random.randint( 0, grid.size[1] - 1 )
        #if j == 0:
        #    pos_x = 660
        #    pos_y = 400
        #else:
        #    pos_x = 690
        #    pos_y = 400
        
        while grid.add_user( User( j, ( pos_x, pos_y ), None, grid ) ) == 0:
            pos_x = random.randint( 0, grid.size[0] - 1 )
            pos_y = random.randint( 0, grid.size[1] - 1 )

                
    return grid

if __name__ == "__main__":          
    guloso = Greedy()
    
    f = open('resumo.csv','w')   # Trying to create a new file or open one
    f.write('TOTAL_BS,TOTAL_RRH,TOTAL_UE,USED_RRH,USER_NOT_MEET,EE,SE\n')
    f.close()
    for qtd_bbu in TOTAL_BBU:
        for qtd_bs in TOTAL_BS:        
            for qtd_rrh in TOTAL_RRH:
                for qtd_ue in TOTAL_UE:
                    for cenario in range( REPETICOES ): #conbinacoes
                        grid = build_scenario(qtd_bbu, qtd_bs, qtd_rrh, qtd_ue )
                        #util.build_KDTree() 
                        util.build_list_users_in_antenna_coverage_area(grid._user, grid.rrh_list)
                        util.build_list_antennas_in_same_coverage_area(grid.rrh_list)
                        #grid.cenario = cenario

                        #grid.build_traffic_user()
		                #grid.print_antennas()
		                #grid.print_users()
                        print qtd_rrh, cenario
                        guloso.run( grid )
		
