"""insert_countries_data, user, company, cliente, proyecto, unidad, orden_de_trabajo

Revision ID: d123c967f10f
Create Date: 2025-06-08 12:35:49.699144

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = 'd123c967f10f'
down_revision = None
branch_labels = None
depends_on = None

# Define the table structure for bulk insert
paises_table = table(
    'paises',
    column('id', sa.Integer),
    column('alpha_2', sa.String),
    column('alpha_3', sa.String), 
    column('nombre', sa.String)
)

def upgrade() -> None:
    # Countries data to insert
    countries_data = [
        {'id': 8, 'alpha_2': 'al', 'alpha_3': 'alb', 'nombre': 'Albania'},
        {'id': 20, 'alpha_2': 'ad', 'alpha_3': 'and', 'nombre': 'Andorra'},
        {'id': 28, 'alpha_2': 'ag', 'alpha_3': 'atg', 'nombre': 'Antigua y Barbuda'},
        {'id': 32, 'alpha_2': 'ar', 'alpha_3': 'arg', 'nombre': 'Argentina'},
        {'id': 36, 'alpha_2': 'au', 'alpha_3': 'aus', 'nombre': 'Australia'},
        {'id': 40, 'alpha_2': 'at', 'alpha_3': 'aut', 'nombre': 'Austria'},
        {'id': 44, 'alpha_2': 'bs', 'alpha_3': 'bhs', 'nombre': 'Bahamas'},
        {'id': 52, 'alpha_2': 'bb', 'alpha_3': 'brb', 'nombre': 'Barbados'},
        {'id': 56, 'alpha_2': 'be', 'alpha_3': 'bel', 'nombre': 'Bélgica'},
        {'id': 84, 'alpha_2': 'bz', 'alpha_3': 'blz', 'nombre': 'Belice'},
        {'id': 112, 'alpha_2': 'by', 'alpha_3': 'blr', 'nombre': 'Bielorrusia'},
        {'id': 68, 'alpha_2': 'bo', 'alpha_3': 'bol', 'nombre': 'Bolivia'},
        {'id': 70, 'alpha_2': 'ba', 'alpha_3': 'bih', 'nombre': 'Bosnia y Herzegovina'},
        {'id': 76, 'alpha_2': 'br', 'alpha_3': 'bra', 'nombre': 'Brasil'},
        {'id': 100, 'alpha_2': 'bg', 'alpha_3': 'bgr', 'nombre': 'Bulgaria'},
        {'id': 124, 'alpha_2': 'ca', 'alpha_3': 'can', 'nombre': 'Canadá'},
        {'id': 152, 'alpha_2': 'cl', 'alpha_3': 'chl', 'nombre': 'Chile'},
        {'id': 170, 'alpha_2': 'co', 'alpha_3': 'col', 'nombre': 'Colombia'},
        {'id': 188, 'alpha_2': 'cr', 'alpha_3': 'cri', 'nombre': 'Costa Rica'},
        {'id': 191, 'alpha_2': 'hr', 'alpha_3': 'hrv', 'nombre': 'Croacia'},
        {'id': 192, 'alpha_2': 'cu', 'alpha_3': 'cub', 'nombre': 'Cuba'},
        {'id': 208, 'alpha_2': 'dk', 'alpha_3': 'dnk', 'nombre': 'Dinamarca'},
        {'id': 212, 'alpha_2': 'dm', 'alpha_3': 'dma', 'nombre': 'Dominica'},
        {'id': 218, 'alpha_2': 'ec', 'alpha_3': 'ecu', 'nombre': 'Ecuador'},
        {'id': 222, 'alpha_2': 'sv', 'alpha_3': 'slv', 'nombre': 'El Salvador'},
        {'id': 703, 'alpha_2': 'sk', 'alpha_3': 'svk', 'nombre': 'Eslovaquia'},
        {'id': 705, 'alpha_2': 'si', 'alpha_3': 'svn', 'nombre': 'Eslovenia'},
        {'id': 724, 'alpha_2': 'es', 'alpha_3': 'esp', 'nombre': 'España'},
        {'id': 840, 'alpha_2': 'us', 'alpha_3': 'usa', 'nombre': 'Estados Unidos'},
        {'id': 233, 'alpha_2': 'ee', 'alpha_3': 'est', 'nombre': 'Estonia'},
        {'id': 246, 'alpha_2': 'fi', 'alpha_3': 'fin', 'nombre': 'Finlandia'},
        {'id': 242, 'alpha_2': 'fj', 'alpha_3': 'fji', 'nombre': 'Fiyi'},
        {'id': 250, 'alpha_2': 'fr', 'alpha_3': 'fra', 'nombre': 'Francia'},
        {'id': 308, 'alpha_2': 'gd', 'alpha_3': 'grd', 'nombre': 'Granada'},
        {'id': 300, 'alpha_2': 'gr', 'alpha_3': 'grc', 'nombre': 'Grecia'},
        {'id': 320, 'alpha_2': 'gt', 'alpha_3': 'gtm', 'nombre': 'Guatemala'},
        {'id': 328, 'alpha_2': 'gy', 'alpha_3': 'guy', 'nombre': 'Guyana'},
        {'id': 332, 'alpha_2': 'ht', 'alpha_3': 'hti', 'nombre': 'Haití'},
        {'id': 340, 'alpha_2': 'hn', 'alpha_3': 'hnd', 'nombre': 'Honduras'},
        {'id': 348, 'alpha_2': 'hu', 'alpha_3': 'hun', 'nombre': 'Hungría'},
        {'id': 372, 'alpha_2': 'ie', 'alpha_3': 'irl', 'nombre': 'Irlanda'},
        {'id': 352, 'alpha_2': 'is', 'alpha_3': 'isl', 'nombre': 'Islandia'},
        {'id': 584, 'alpha_2': 'mh', 'alpha_3': 'mhl', 'nombre': 'Islas Marshall'},
        {'id': 90, 'alpha_2': 'sb', 'alpha_3': 'slb', 'nombre': 'Islas Salomón'},
        {'id': 380, 'alpha_2': 'it', 'alpha_3': 'ita', 'nombre': 'Italia'},
        {'id': 388, 'alpha_2': 'jm', 'alpha_3': 'jam', 'nombre': 'Jamaica'},
        {'id': 428, 'alpha_2': 'lv', 'alpha_3': 'lva', 'nombre': 'Letonia'},
        {'id': 438, 'alpha_2': 'li', 'alpha_3': 'lie', 'nombre': 'Liechtenstein'},
        {'id': 440, 'alpha_2': 'lt', 'alpha_3': 'ltu', 'nombre': 'Lituania'},
        {'id': 442, 'alpha_2': 'lu', 'alpha_3': 'lux', 'nombre': 'Luxemburgo'},
        {'id': 807, 'alpha_2': 'mk', 'alpha_3': 'mkd', 'nombre': 'Macedonia del Norte'},
        {'id': 470, 'alpha_2': 'mt', 'alpha_3': 'mlt', 'nombre': 'Malta'},
        {'id': 484, 'alpha_2': 'mx', 'alpha_3': 'mex', 'nombre': 'México'},
        {'id': 583, 'alpha_2': 'fm', 'alpha_3': 'fsm', 'nombre': 'Micronesia'},
        {'id': 498, 'alpha_2': 'md', 'alpha_3': 'mda', 'nombre': 'Moldavia'},
        {'id': 492, 'alpha_2': 'mc', 'alpha_3': 'mco', 'nombre': 'Mónaco'},
        {'id': 499, 'alpha_2': 'me', 'alpha_3': 'mne', 'nombre': 'Montenegro'},
        {'id': 520, 'alpha_2': 'nr', 'alpha_3': 'nru', 'nombre': 'Nauru'},
        {'id': 558, 'alpha_2': 'ni', 'alpha_3': 'nic', 'nombre': 'Nicaragua'},
        {'id': 578, 'alpha_2': 'no', 'alpha_3': 'nor', 'nombre': 'Noruega'},
        {'id': 554, 'alpha_2': 'nz', 'alpha_3': 'nzl', 'nombre': 'Nueva Zelanda'},
        {'id': 528, 'alpha_2': 'nl', 'alpha_3': 'nld', 'nombre': 'Países Bajos'},
        {'id': 585, 'alpha_2': 'pw', 'alpha_3': 'plw', 'nombre': 'Palaos'},
        {'id': 591, 'alpha_2': 'pa', 'alpha_3': 'pan', 'nombre': 'Panamá'},
        {'id': 598, 'alpha_2': 'pg', 'alpha_3': 'png', 'nombre': 'Papúa Nueva Guinea'},
        {'id': 600, 'alpha_2': 'py', 'alpha_3': 'pry', 'nombre': 'Paraguay'},
        {'id': 604, 'alpha_2': 'pe', 'alpha_3': 'per', 'nombre': 'Perú'},
        {'id': 616, 'alpha_2': 'pl', 'alpha_3': 'pol', 'nombre': 'Polonia'},
        {'id': 620, 'alpha_2': 'pt', 'alpha_3': 'prt', 'nombre': 'Portugal'},
        {'id': 826, 'alpha_2': 'gb', 'alpha_3': 'gbr', 'nombre': 'Reino Unido'},
        {'id': 203, 'alpha_2': 'cz', 'alpha_3': 'cze', 'nombre': 'República Checa'},
        {'id': 214, 'alpha_2': 'do', 'alpha_3': 'dom', 'nombre': 'República Dominicana'},
        {'id': 642, 'alpha_2': 'ro', 'alpha_3': 'rou', 'nombre': 'Rumania'},
        {'id': 643, 'alpha_2': 'ru', 'alpha_3': 'rus', 'nombre': 'Rusia'},
        {'id': 882, 'alpha_2': 'ws', 'alpha_3': 'wsm', 'nombre': 'Samoa'},
        {'id': 659, 'alpha_2': 'kn', 'alpha_3': 'kna', 'nombre': 'San Cristóbal y Nieves'},
        {'id': 674, 'alpha_2': 'sm', 'alpha_3': 'smr', 'nombre': 'San Marino'},
        {'id': 670, 'alpha_2': 'vc', 'alpha_3': 'vct', 'nombre': 'San Vicente y las Granadinas'},
        {'id': 662, 'alpha_2': 'lc', 'alpha_3': 'lca', 'nombre': 'Santa Lucía'},
        {'id': 678, 'alpha_2': 'st', 'alpha_3': 'stp', 'nombre': 'Santo Tomé y Príncipe'},
        {'id': 688, 'alpha_2': 'rs', 'alpha_3': 'srb', 'nombre': 'Serbia'},
        {'id': 752, 'alpha_2': 'se', 'alpha_3': 'swe', 'nombre': 'Suecia'},
        {'id': 756, 'alpha_2': 'ch', 'alpha_3': 'che', 'nombre': 'Suiza'},
        {'id': 740, 'alpha_2': 'sr', 'alpha_3': 'sur', 'nombre': 'Surinam'},
        {'id': 776, 'alpha_2': 'to', 'alpha_3': 'ton', 'nombre': 'Tonga'},
        {'id': 780, 'alpha_2': 'tt', 'alpha_3': 'tto', 'nombre': 'Trinidad y Tobago'},
        {'id': 804, 'alpha_2': 'ua', 'alpha_3': 'ukr', 'nombre': 'Ucrania'},
        {'id': 858, 'alpha_2': 'uy', 'alpha_3': 'ury', 'nombre': 'Uruguay'},
        {'id': 548, 'alpha_2': 'vu', 'alpha_3': 'vut', 'nombre': 'Vanuatu'},
        {'id': 862, 'alpha_2': 've', 'alpha_3': 'ven', 'nombre': 'Venezuela'},
    ]
    
    # Use bulk insert for better performance
    op.bulk_insert(paises_table, countries_data)


def downgrade() -> None:
    # Remove all inserted countries
    op.execute("DELETE FROM paises WHERE id IN (8,20,28,32,36,40,44,52,56,84,112,68,70,76,100,124,152,170,188,191,192,208,212,218,222,703,705,724,840,233,246,242,250,308,300,320,328,332,340,348,372,352,584,90,380,388,428,438,440,442,807,470,484,583,498,492,499,520,558,578,554,528,585,591,598,600,604,616,620,826,203,214,642,643,882,659,674,670,662,678,688,752,756,740,776,780,804,858,548,862)") 