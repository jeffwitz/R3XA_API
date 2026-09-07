from dataclasses import dataclass, field

@dataclass
class Case:
    id: str
    name: str
    parent_ids: list[str] = field(default_factory=list)
    color: str = "white"
    text_color: str = "white"

from pathlib import Path
import math
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path as MplPath
import networkx as nx

# ============================================================
# PARAMÈTRES
# ============================================================

OUTPUT_FILE = "r3xa_flowchart.png"

FIGURE_SIZE = (16, 10)
DPI = 180

# Taille minimale d'une case
MIN_NODE_WIDTH = 1.5

# Taille maximale d'une case
MAX_NODE_WIDTH = 125.0

# Hauteur de chaque ligne de texte
LINE_HEIGHT = 0.32

# Marge horizontale autour du texte
TEXT_HORIZONTAL_PADDING = 0.5

# Marge verticale autour du texte
TEXT_VERTICAL_PADDING = 0.5

# Taille du texte
FONT_SIZE = 10

# Rayon des coins arrondis
NODE_ROUNDING = 0.15

# Placement automatique
LAYOUT_K = 3.0
LAYOUT_ITERATIONS = 500

# Marge autour du graphe
GRAPH_MARGIN = 2.0


# ============================================================
# CONSTRUCTION DU GRAPHE
# ============================================================

def build_graph(data):
    """
    Construit un graphe NetworkX à partir d'une liste de Case.

    Chaque Case doit posséder :

        id
        name
        parent_ids
        color
        text_color
    """

    G = nx.DiGraph()

    # --------------------------------------------------------
    # Ajout des nœuds
    # --------------------------------------------------------

    for case in data:

        G.add_node(
            case.id,
            name=case.name,
            color=case.color,
            text_color=case.text_color,
        )

    # --------------------------------------------------------
    # Ajout des relations parent -> enfant
    # --------------------------------------------------------

    for case in data:

        for parent_id in case.parent_ids:

            if parent_id not in G:

                raise ValueError(
                    f"Le parent '{parent_id}' "
                    f"du nœud '{case.id}' "
                    f"('{case.name}') "
                    "n'existe pas dans les données."
                )

            G.add_edge(
                parent_id,
                case.id,
            )

    return G


# ============================================================
# CALCUL DE LA TAILLE DES CASES
# ============================================================

def calculate_node_sizes(G):
    """
    Calcule une largeur et une hauteur pour chaque nœud
    en fonction de la longueur de son texte.

    Les dimensions sont stockées directement dans le graphe.
    """

    for node_id, attributes in G.nodes(data=True):

        name = attributes["name"]

        # ----------------------------------------------------
        # Estimation simple de la largeur du texte
        #
        # 0.09 est une approximation raisonnable pour une
        # police de taille 10.
        # ----------------------------------------------------

        estimated_width = (
            len(name) * 0.09
            + TEXT_HORIZONTAL_PADDING
        )

        # Limitation de la largeur
        width = min(
            max(
                estimated_width,
                MIN_NODE_WIDTH,
            ),
            MAX_NODE_WIDTH,
        )
        print(width)

        # ----------------------------------------------------
        # Si le texte dépasse la largeur maximale,
        # on le découpe en plusieurs lignes.
        # ----------------------------------------------------

        # Approximation du nombre de caractères par ligne
        chars_per_line = max(
            1,
            int(
                (
                    MAX_NODE_WIDTH
                    - TEXT_HORIZONTAL_PADDING
                )
                / 0.09
            )
        )

        lines = textwrap.wrap(
            name,
            width=chars_per_line,
            break_long_words=False,
            break_on_hyphens=False,
        )

        # Évite qu'un texte très court soit inutilement
        # traité comme plusieurs lignes
        if not lines:
            lines = [name]

        # ----------------------------------------------------
        # Hauteur en fonction du nombre de lignes
        # ----------------------------------------------------

        height = (
            len(lines) * LINE_HEIGHT
            + TEXT_VERTICAL_PADDING
        )

        # ----------------------------------------------------
        # Stockage des informations
        # ----------------------------------------------------

        attributes["width"] = width
        attributes["height"] = height
        attributes["display_name"] = "\n".join(lines)


# ============================================================
# DESSIN D'UNE LIAISON COURBE
# ============================================================

def bezier_edge(
    ax,
    p1,
    p2,
    rad=0.20,
    linewidth=1.4,
    alpha=0.65,
):
    """
    Dessine une courbe de Bézier quadratique entre deux points.
    """

    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1

    length = math.hypot(
        dx,
        dy,
    )

    if length == 0:
        return

    # --------------------------------------------------------
    # Vecteur perpendiculaire
    # --------------------------------------------------------

    nxp = -dy / length
    nyp = dx / length

    # --------------------------------------------------------
    # Point de contrôle
    # --------------------------------------------------------

    cx = (
        (x1 + x2) / 2
        + nxp * length * rad
    )

    cy = (
        (y1 + y2) / 2
        + nyp * length * rad
    )

    # --------------------------------------------------------
    # Courbe de Bézier
    # --------------------------------------------------------

    path = MplPath(
        [
            (x1, y1),
            (cx, cy),
            (x2, y2),
        ],
        [
            MplPath.MOVETO,
            MplPath.CURVE3,
            MplPath.CURVE3,
        ],
    )

    patch = PathPatch(
        path,
        facecolor="none",
        edgecolor="black",
        linewidth=linewidth,
        alpha=alpha,
        zorder=1,
    )

    ax.add_patch(patch)


# ============================================================
# DESSIN D'UNE CASE
# ============================================================

def draw_node(
    ax,
    x,
    y,
    name,
    color,
    text_color,
    width,
    height,
):
    """
    Dessine une case dont la taille dépend du texte.
    """

    # --------------------------------------------------------
    # Case arrondie
    # --------------------------------------------------------

    box = FancyBboxPatch(
        (
            x - width / 2,
            y - height / 2,
        ),

        width,
        height,

        boxstyle=(
            f"round,pad=0.02,"
            f"rounding_size={NODE_ROUNDING}"
        ),

        facecolor=color,
        edgecolor="black",
        linewidth=1.2,

        zorder=3,
    )

    ax.add_patch(box)

    # --------------------------------------------------------
    # Texte
    # --------------------------------------------------------

    ax.text(
        x,
        y,
        name,

        ha="center",
        va="center",

        fontsize=FONT_SIZE,

        color=text_color,

        multialignment="center",

        zorder=4,
    )


# ============================================================
# CRÉATION DU FLOWCHART
# ============================================================

def create_flowchart(
    data,
    output_file=OUTPUT_FILE,
):
    """
    Génère un flowchart à partir d'une liste de Case.
    """

    # --------------------------------------------------------
    # Construction du graphe
    # --------------------------------------------------------

    G = build_graph(data)

    # --------------------------------------------------------
    # Calcul de la taille des cases
    # --------------------------------------------------------

    calculate_node_sizes(G)

    # --------------------------------------------------------
    # Placement automatique
    # --------------------------------------------------------

    pos = nx.spring_layout(
        G,

        seed=42,

        k=LAYOUT_K,

        iterations=LAYOUT_ITERATIONS,

        scale=10,
    )

    # --------------------------------------------------------
    # Création de la figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=FIGURE_SIZE
    )

    # --------------------------------------------------------
    # Dessin des liens
    # --------------------------------------------------------

    for i, (parent, child) in enumerate(
        G.edges()
    ):

        x1, y1 = pos[parent]
        x2, y2 = pos[child]

        # Courbures différentes pour les liens
        # afin d'éviter qu'ils se superposent.
        rad_values = [
            -0.18,
            0.18,
            -0.28,
            0.28,
        ]

        rad = rad_values[
            i % len(rad_values)
        ]

        bezier_edge(
            ax,
            (x1, y1),
            (x2, y2),
            rad=rad,
        )

    # --------------------------------------------------------
    # Dessin des cases
    # --------------------------------------------------------

    for node_id, attributes in G.nodes(
        data=True
    ):

        x, y = pos[node_id]

        draw_node(
            ax,
            x,
            y,

            attributes["display_name"],

            attributes["color"],

            attributes["text_color"],

            attributes["width"],

            attributes["height"],
        )

    # --------------------------------------------------------
    # Mise en page
    # --------------------------------------------------------

    ax.set_aspect("equal")

    ax.axis("off")

    # --------------------------------------------------------
    # Calcul des limites
    # --------------------------------------------------------

    xs = [
        p[0]
        for p in pos.values()
    ]

    ys = [
        p[1]
        for p in pos.values()
    ]

    ax.set_xlim(
        min(xs) - GRAPH_MARGIN,
        max(xs) + GRAPH_MARGIN,
    )

    ax.set_ylim(
        min(ys) - GRAPH_MARGIN,
        max(ys) + GRAPH_MARGIN,
    )

    plt.tight_layout()

    # --------------------------------------------------------
    # Sauvegarde
    # --------------------------------------------------------

    output_path = Path(
        output_file
    )

    fig.savefig(
        output_path,
        dpi=DPI,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    print(
        f"Image générée : "
        f"{output_path.resolve()}"
    )


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================


data = [Case(id='fzdnbdqklekfqthwjkbagqry', name='Calibration board', parent_ids=[], color='#c4894f', text_color='white'), 
        Case(id='esepjdxthdxbuvoijwgvzhsy', name='StereoRig', parent_ids=[], color='#c4894f', text_color='white'), 
        Case(id='aibfimxqmyovilpvrguqjicf', name='Camera 0', parent_ids=['esepjdxthdxbuvoijwgvzhsy'], color='#bf0040', text_color='white'), 
        Case(id='tsllmhxilpqkxbaituxzvyjn', name='Camera 1', parent_ids=['esepjdxthdxbuvoijwgvzhsy'], color='#bf0040', text_color='white'), 
        Case(id='ftatwplfdyrgacmpphifpbuv', name='Calibration Tool', parent_ids=['fzdnbdqklekfqthwjkbagqry', 'kvydlmfdfjwsvlhnvtnamepp', 'izykucgqplhjzekbyoxbznwu'], color='#bf0040', text_color='white'), 
        Case(id='jwawuzwyhhievfyfnqewjyuo', name='Stereo DIC', parent_ids=['egaohsywiawjdkhwbaazfodj', 'qvvxsqaonuzhmyzixcnofhbx', 'uccmltffnomebweqejcoinlc'], color='#bf0040', text_color='white'), 
        Case(id='kvydlmfdfjwsvlhnvtnamepp', name='left calib img', parent_ids=['aibfimxqmyovilpvrguqjicf'], color='#038181', text_color='white'), 
        Case(id='izykucgqplhjzekbyoxbznwu', name='right calib img', parent_ids=['tsllmhxilpqkxbaituxzvyjn'], color='#038181', text_color='white'), 
        Case(id='uccmltffnomebweqejcoinlc', name='Calibration parameters', parent_ids=['ftatwplfdyrgacmpphifpbuv'], color='#038181', text_color='white'), 
        Case(id='egaohsywiawjdkhwbaazfodj', name='left images', parent_ids=['aibfimxqmyovilpvrguqjicf'], color='#038181', text_color='white'), 
        Case(id='qvvxsqaonuzhmyzixcnofhbx', name='right images', parent_ids=['tsllmhxilpqkxbaituxzvyjn'], color='#038181', text_color='white'), 
        Case(id='rwaxqewgaawrtmiscmqzyona', name='DIC Displacement', parent_ids=['jwawuzwyhhievfyfnqewjyuo'], color='#038181', text_color='white')]


create_flowchart(data, "r3xa_flowchart.png")
