from ipywidgets import (
    HBox,
    VBox,
    IntSlider,
    SelectMultiple,
    FloatLogSlider,
    FloatSlider,
    AppLayout,
    TwoByTwoLayout,
    Label,
    Layout,
    Button,
    Textarea,
)
from functools import reduce
from bqplot import *
from bqplot.marks import Graph
from efficient_apriori import apriori
from pathlib import Path

# import time
import datetime


class Arulesviz:
    def __init__(
        self,
        transactions,
        min_sup,
        min_conf,
        min_lift,
        max_sup=1.0,
        min_slift=0.1,
        products_to_drop=[],
    ):
        self.rules = []
        self.transactions = transactions
        self.min_lift = min_lift
        self.min_slift = min_slift
        self.min_slift = min_slift or min_lift
        self.min_sup = min_sup
        self.min_conf = min_conf
        self.max_sup = max_sup
        self.products_to_in = []
        self.products_to_out = products_to_drop
        self._hovered_product = None

    def _standardized_lift(self, rule, s=None, c=None):
        """
        Parameters
        ----------
        rule:
              Target rule
        s: float
           Support treshold user for rule mining
        c: float
           Confidence treshold user for rule mining
        """
        s = s or self.min_sup
        c = c or self.min_conf
        prob_A = getattr(rule, "support") / getattr(rule, "confidence")
        prob_B = getattr(rule, "confidence") / getattr(rule, "lift")
        mult_A_and_B = prob_A * prob_B
        L = max(
            1 / prob_A + 1 / prob_B - 1 / (mult_A_and_B),
            s / mult_A_and_B,
            c / prob_B,
            0,
        )
        U = min(1 / prob_A, 1 / prob_B)
        slift = (getattr(rule, "lift") - L) / (U - L)
        return slift

    def create_rules(self, drop_products=True, max_sup=None):
        max_sup = max_sup or self.max_sup
        tr = self.transactions
        if drop_products:
            to_drop = set(self.products_to_out)
            tr = [set(x) - to_drop for x in tr]
            tr = [x for x in tr if x]
        _, self.rules = apriori(
            tr, min_support=self.min_sup, min_confidence=self.min_conf
        )
        for rule in self.rules:
            setattr(rule, "slift", self._standardized_lift(rule))
        self.rules = self.filter_numeric(
            "support", max_sup, self.rules, should_be_lower=True
        )
        self._max_sup = max([x.support for x in self.rules])
        self._max_conf = max([x.confidence for x in self.rules])

    def filter_numeric(self, atr, val, rules, should_be_lower=False):
        rules = rules
        if should_be_lower:
            return [x for x in rules if getattr(x, atr) < val]
        return [x for x in rules if getattr(x, atr) > val]

    def filter_drop_if_name_in(self, vals, rules, lhs=True, rhs=True):
        rules = rules
        vals = set(vals)
        f = lambda x: not any(
            [(lhs and (vals & set(x.lhs))), (rhs and (vals & set(x.rhs)))]
        )
        return list(filter(f, rules))

    def filter_drop_if_name_out(self, vals, rules, lhs=True, rhs=True):
        rules = rules
        vals = set(vals)
        f = lambda x: any(
            [(lhs and (vals & set(x.lhs))), (rhs and (vals & set(x.rhs)))]
        )
        return list(filter(f, rules))

    def get_unique_products(self, rules):
        rules = rules
        return reduce(
            lambda x, y: (x if isinstance(x, set) else set(x.lhs) | set(x.rhs))
            | set(y.lhs)
            | set(y.rhs),
            rules,
        )

    def create_graph(self, rules):
        rules = rules
        nodes = []
        links = []
        colors = []
        name_to_id = {}
        already_seen = set()
        for sr in rules:
            current_comb = tuple(sorted(set(sr.lhs) | set(sr.rhs)))
            if current_comb in already_seen:
                continue
            else:
                already_seen.add(current_comb)
            # node_size = max(min(sr.lift * 10, 30), 5)
            nodes.append(
                {
                    "label": f".",
                    "shape": "circle",
                    "shape_attrs": {"r": max(min(sr.lift, 7), 2)},
                    "is_rule": True,
                    "tooltip": str(sr),
                }
            )
            colors.append("black")
            rule_id = len(nodes) - 1

            for node_name in sr.lhs:
                l_node_id = name_to_id.get(node_name, None)
                if l_node_id == None:
                    nodes.append(
                        {
                            "label": node_name,
                            "shape": "rect",
                            "is_rule": False,
                            "shape_attrs": {
                                "width": 6 * len(node_name) + 8,
                                "height": 20,
                            },
                        }
                    )
                    colors.append("white")
                    l_node_id = len(nodes) - 1
                    name_to_id[node_name] = l_node_id
                links.append({"source": l_node_id, "target": rule_id, "value": sr.lift})

            for node_name in sr.rhs:
                r_node_id = name_to_id.get(node_name, None)
                if r_node_id == None:
                    nodes.append(
                        {
                            "label": node_name,
                            "shape": "rect",
                            "is_rule": False,
                            "shape_attrs": {
                                "width": 6 * len(node_name) + 8,
                                "height": 20,
                            },
                        }
                    )
                    r_node_id = len(nodes) - 1
                    name_to_id[node_name] = r_node_id
                    colors.append("white")
                links.append({"source": rule_id, "target": r_node_id, "value": sr.lift})
        return nodes, links, colors

    def replot_graph(self):
        sub_rules = self.filter_numeric("lift", self.min_lift, rules=self.rules)
        sub_rules = self.filter_numeric("support", self.min_sup, rules=sub_rules)
        sub_rules = self.filter_numeric("slift", self.min_slift, rules=sub_rules)
        sub_rules = self.filter_numeric("confidence", self.min_conf, rules=sub_rules)
        sub_rules = self.filter_drop_if_name_in(self.products_to_out, rules=sub_rules)
        sub_rules = self.filter_drop_if_name_out(self.products_to_in, rules=sub_rules)
        (
            self.graph.node_data,
            self.graph.link_data,
            _,  # self.graph.colors,
        ) = self.create_graph(sub_rules)

    def handler_products_out_filter(self, value):
        self.products_to_out = value["new"]
        self.replot_graph()

    def setup_products_out_selector(self):
        self.selector_products_out = SelectMultiple(
            options=sorted(self.get_unique_products(self.rules)),
            value=[],
            rows=10,
            # description="Drop",
            disabled=False,
        )
        self.selector_products_out.observe(self.handler_products_out_filter, "value")

    def handler_products_in_filter(self, value):
        self.products_to_in = value["new"]
        self.replot_graph()

    def setup_products_in_selector(self):
        self.selector_products_in = SelectMultiple(
            options=sorted(self.get_unique_products(self.rules)),
            value=sorted(self.get_unique_products(self.rules)),
            rows=10,
            # description="Include",
            disabled=False,
        )
        self.products_to_in = sorted(self.get_unique_products(self.rules))
        self.selector_products_in.observe(self.handler_products_in_filter, "value")

    def set_slider_value(self, value):
        setattr(self, getattr(value["owner"], "description"), value["new"])
        self.replot_graph()

    def setup_lift_slider(self):
        name = "lift"
        setattr(
            self,
            f"slider_{name}",
            FloatLogSlider(
                value=getattr(self, f"min_{name}"),
                min=-0.5,
                max=1.5,
                step=0.05,
                base=10,
                description=f"min_{name}",
                disabled=False,
                continuous_update=False,
                orientation="horizontal",
                readout=True,
                readout_format=".3f",
            ),
        )
        getattr(self, f"slider_{name}").observe(self.set_slider_value, "value")

    def setup_conf_slider(self):
        name = "conf"
        setattr(
            self,
            f"slider_{name}",
            FloatSlider(
                value=getattr(self, f"min_{name}"),
                min=0.0,
                max=self._max_conf,
                step=0.0001,
                base=10,
                description=f"min_{name}",
                disabled=False,
                continuous_update=False,
                orientation="horizontal",
                readout=True,
                readout_format=".5f",
            ),
        )
        getattr(self, f"slider_{name}").observe(self.set_slider_value, "value")

    def setup_slift_slider(self):
        name = "slift"
        setattr(
            self,
            f"slider_{name}",
            FloatSlider(
                value=getattr(self, f"min_{name}"),
                min=0.0,
                max=1.0,
                step=0.0001,
                base=10,
                description=f"min_{name}",
                disabled=False,
                continuous_update=False,
                orientation="horizontal",
                readout=True,
                readout_format=".5f",
            ),
        )
        getattr(self, f"slider_{name}").observe(self.set_slider_value, "value")

    def setup_sup_slider(self):
        name = "sup"
        setattr(
            self,
            f"slider_{name}",
            FloatSlider(
                value=getattr(self, f"min_{name}"),
                min=0.0,
                max=self._max_sup,
                step=0.0001,
                base=10,
                description=f"min_{name}",
                disabled=False,
                continuous_update=False,
                orientation="horizontal",
                readout=True,
                readout_format=".5f",
            ),
        )
        getattr(self, f"slider_{name}").observe(self.set_slider_value, "value")

    def _save_graph_img(self, b):
        self.fig.save_png(
            f"arulesviz_{datetime.datetime.now().isoformat().replace(':','-').split('.')[0]}.png"
        )

    def setup_graph_to_img_button(self):
        self.graph_to_img_button = Button(description="Save img!")
        self.graph_to_img_button.on_click(self._save_graph_img)

    def plot_graph(
        self,
        width=1000,
        height=750,
        charge=-200,
        link_type="arc",
        directed=True,
        link_distance=100,
    ):
        fig_layout = Layout(width=f"{width}px", height=f"{height}px")
        nodes, links, colors = self.create_graph(
            self.filter_numeric("lift", self.min_lift, rules=self.rules)
        )
        # xs = LinearScale(min=0, max=1000)
        # ys = LinearScale(min=0, max=750)
        cs = ColorScale(scheme="Reds")
        self.graph = Graph(
            node_data=nodes,
            link_data=links,
            # colors=colors,
            charge=charge,
            link_type=link_type,
            directed=directed,
            link_distance=link_distance,
            # scales={'color': cs}
        )
        margin = dict(top=-60, bottom=-60, left=-60, right=-60)
        self.fig = Figure(
            marks=[self.graph],
            layout=Layout(width=f"{width}px", height=f"{height}px"),
            fig_margin=dict(top=0, bottom=0, left=0, right=0),
            legend_text={"font-size": 7},
        )

        # tooltip = Tooltip(fields=["foo"], formats=["", "", ""])
        # self.graph.tooltip = tooltip

        # self.graph.on_hover(self.hover_handler)
        self.graph.on_element_click(self.hover_handler)
        self.graph.on_background_click(self.clean_tooltip)
        self.graph.interactions = {"click": "tooltip"}
        self.setup_sup_slider()
        self.setup_lift_slider()
        self.setup_conf_slider()
        self.setup_slift_slider()
        self.setup_products_in_selector()
        self.setup_products_out_selector()
        self.setup_graph_to_img_button()
        self.setup_product_tooltip()
        return VBox(
            [
                HBox(
                    [
                        self.selector_products_in,
                        self.selector_products_out,
                        VBox(
                            [
                                getattr(self, "slider_lift"),
                                getattr(self, "slider_slift"),
                                getattr(self, "slider_conf"),
                                getattr(self, "slider_sup"),
                            ]
                        ),
                        getattr(self, "graph_to_img_button"),
                    ]
                ),
                self.fig,
            ]
        )

    def clean_tooltip(self, x, y):
        self.graph.tooltip = None

    def plot_scatter(
        self,
        products=[],
        min_width=600,
        min_height=600,
        max_width=600,
        max_height=600,
        with_toolbar=True,
        display_names=False,
    ):
        if products:
            sub_rules = self.filter_drop_if_name_out(products, self.rules)
        else:
            sub_rules = self.rules
        data_x = [np.round(x.support * 100, 3) for x in sub_rules]
        data_y = [np.round(x.confidence * 100, 3) for x in sub_rules]
        color = [np.round(x.lift, 4) for x in sub_rules]
        names = [str(sr) for sr in sub_rules]
        sc_x = LinearScale()
        sc_y = LinearScale()
        sc_color = ColorScale(scheme="Reds")
        ax_c = ColorAxis(
            scale=sc_color,
            tick_format="",
            label="Lift",
            orientation="vertical",
            side="right",
        )
        tt = Tooltip(fields=["name"], formats=[""])
        scatt = Scatter(
            x=data_x,
            y=data_y,
            color=color,
            scales={"x": sc_x, "y": sc_y, "color": sc_color},
            tooltip=tt,
            names=names,
            display_names=display_names,
        )
        ax_x = Axis(scale=sc_x, label="Sup*100")
        ax_y = Axis(scale=sc_y, label="Conf*100", orientation="vertical")
        m_chart = dict(top=50, bottom=70, left=50, right=100)
        fig = Figure(
            marks=[scatt],
            axes=[ax_x, ax_y, ax_c],
            fig_margin=m_chart,
            layout=Layout(
                min_width=f"{min_width}px",
                min_height=f"{min_height}px",
                max_width=f"{max_width}px",
                max_height=f"{max_height}px",
            ),
        )
        if with_toolbar:
            toolbar = Toolbar(figure=fig)
            return VBox([fig, toolbar])
        else:
            return fig

    def setup_product_tooltip(self, products=[]):
        self.graph.tooltip = self.plot_scatter(products)
        if len(products) == 1:
            self.graph.tooltip.title = products[-1]
        else:
            self.graph.tooltip.title = "Products scatter"

    def hover_handler(self, qq, content):
        product = content.get("data", {}).get("label", -1)
        is_rule = content.get("data", {}).get("tooltip", None)
        if product != self._hovered_product:
            if is_rule:
                self._hovered_product = content.get("data", {}).get("tooltip", None)
                self.graph.tooltip = Textarea(
                    content.get("data", {}).get("tooltip", None)
                )
                self.graph.tooltip_location = "center"
            else:
                self._hovered_product = product
                self.setup_product_tooltip([product])
                self.graph.tooltip_location = "center"
