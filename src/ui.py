
from textual.binding import Binding
from textual.reactive import reactive
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, VerticalScroll
from textual.widgets import Header, Footer, Static, DataTable, Sparkline, Label, TabbedContent, TabPane

from .monitor import get_amd_gpus, AMDGPU

class GPUSparklines(Static):
    def __init__(self, gpu: AMDGPU):
        super().__init__()
        self.gpu = gpu

    DEFAULT_CSS = """
    .load-sparkline {
        color: green;
    }
    .temp-sparkline {
        color: red;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(classes="sparkline-container"):
            yield Label(f"Load: {self.gpu.current_load}%", id=f"spk-load-{self.gpu.id}")
            yield Sparkline(self.gpu.history_load, summary_function=max, classes="load-sparkline")

            yield Label(f"Temp: {self.gpu.current_temp}°C", id=f"spk-temp-{self.gpu.id}")
            yield Sparkline(self.gpu.history_temp, summary_function=max, classes="temp-sparkline")

    def update_data(self):
        load_spark = self.query(Sparkline)[0]
        temp_spark = self.query(Sparkline)[1]
        
        load_spark.data = list(self.gpu.history_load)
        temp_spark.data = list(self.gpu.history_temp)
        
        self.query_one(f"#spk-load-{self.gpu.id}", Label).update(f"Load: {self.gpu.current_load}%")
        self.query_one(f"#spk-temp-{self.gpu.id}", Label).update(f"Temp: {self.gpu.current_temp:.1f}°C")


class GPUCard(Static):
    DEFAULT_CSS = """
    GPUCard {
        border: solid green;
        padding: 1;
        margin: 1;
        height: auto;
        min-height: 20;
        width: 100%;
    }
    .metrics {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
    }
    """

    def __init__(self, gpu: AMDGPU):
        super().__init__()
        self.gpu        = gpu
        self.sparklines = GPUSparklines(gpu)

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.gpu.id}] {self.gpu.model_name}", classes="title")
        yield Label("---")
        with Container(classes="metrics"):
            yield Label(id=f"temp-{self.gpu.id}")
            yield Label(id=f"temp-junc-{self.gpu.id}")
            yield Label(id=f"temp-mem-{self.gpu.id}")
            
            yield Label(id=f"load-{self.gpu.id}")
            
            yield Label(id=f"power-{self.gpu.id}")
            yield Label(id=f"voltage-{self.gpu.id}")
            
            yield Label(id=f"fan-{self.gpu.id}")
            yield Label(id=f"vram-{self.gpu.id}")
            yield Label(id=f"clock-{self.gpu.id}")
            yield Label(id=f"pcie-{self.gpu.id}")
        
        yield self.sparklines

    def on_mount(self) -> None:
        self.update_stats()

    def update_view(self) -> None:
        self.update_stats()

    def update_stats(self) -> None:
        m = self.gpu.get_metrics_dict()

        self.query_one(f"#temp-{self.gpu.id}",      Label).update(f"Edge: {m['temp']:.1f}°C")
        self.query_one(f"#temp-junc-{self.gpu.id}", Label).update(f"Junc: {m['temp_junction']:.1f}°C")
        self.query_one(f"#temp-mem-{self.gpu.id}",  Label).update(f"Mem:  {m['temp_mem']:.1f}°C")

        self.query_one(f"#load-{self.gpu.id}", Label).update(f"Load: {m['load']}%")

        p_cap = f"/{m['power_cap']:.0f}W" if m['power_cap'] > 0 else ""
        self.query_one(f"#power-{self.gpu.id}",   Label).update(f"Pwr:  {m['power']:.1f}{p_cap}")
        self.query_one(f"#voltage-{self.gpu.id}", Label).update(f"Volt: {m['voltage']:.3f}V")

        self.query_one(f"#fan-{self.gpu.id}",   Label).update(f"Fan:  {m['fan']} RPM")
        self.query_one(f"#vram-{self.gpu.id}",  Label).update(f"VRAM: {m['vram_used']}/{m['vram_total']} MiB")
        self.query_one(f"#clock-{self.gpu.id}", Label).update(f"Clk:  {m['sclk']}/{m['mclk']} MHz")
        self.query_one(f"#pcie-{self.gpu.id}",  Label).update(f"PCIe: {m['pcie']}")

        self.sparklines.update_data()


class MonitorApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    .title {
        text-style: bold;
        color: cyan;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
        Binding("r", "refresh_gpus", "Rescan GPUs"),
    ]

    def __init__(self):
        super().__init__()
        self.gpus = get_amd_gpus()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        
        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard", id="dashboard"):
                if not self.gpus:
                     yield Label("No AMD GPUs found! Check permissions or drivers.", id="no-gpu")
                else:
                    with VerticalScroll():
                         for gpu in self.gpus:
                             yield GPUCard(gpu)
            
            with TabPane("Details Table", id="details"):
                 yield DataTable()

            with TabPane("Logs", id="logs"):
                 yield Label("Coming soon...")

    def on_mount(self) -> None:
        self.populate_table()
        self.set_interval(1.0, self.on_update_tick)

    def on_update_tick(self) -> None:
        for gpu in self.gpus:
            gpu.refresh()

        for card in self.query(GPUCard):
            card.update_view()

        self.update_table()

    def populate_table(self):
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Model", "Temp", "Load", "VRAM", "Power", "Fan")
        for gpu in self.gpus:
             m = gpu.get_metrics_dict()
             table.add_row(
                 gpu.id,
                 gpu.model_name,
                 f"{m['temp']:.1f}",
                 f"{m['load']}",
                 f"{m['vram_used']}/{m['vram_total']}",
                 f"{m['power']:.1f}",
                 f"{m['fan']}",
                 key=gpu.id
             )

    def update_table(self):
        table = self.query_one(DataTable)
        for gpu in self.gpus:
             m = gpu.get_metrics_dict()
             try:
                 table.update_cell(gpu.id, "Temp", f"{m['temp']:.1f}")
                 table.update_cell(gpu.id, "Load", f"{m['load']}")
                 table.update_cell(gpu.id, "VRAM", f"{m['vram_used']}/{m['vram_total']}")
                 table.update_cell(gpu.id, "Power", f"{m['power']:.1f}")
                 table.update_cell(gpu.id, "Fan", f"{m['fan']}")
             except Exception:
                 pass

    def action_refresh_gpus(self):
        self.gpus = get_amd_gpus()
        self.notify("GPU List rescanned (restart app to reflect layout changes)")