"""Benchmarks for database.py – SQLite CRUD operations."""
import os, sys, shutil, tempfile, uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmarks.base_benchmark import BaseBenchmark
from benchmarks._st_mock import install_streamlit_mock, remove_streamlit_mock


class DatabaseBenchmark(BaseBenchmark):
    SUITE_NAME = "Database Operations"

    def setup(self):
        install_streamlit_mock()
        self._tmp = tempfile.mkdtemp(prefix="eco_bench_")
        import importlib, database
        importlib.reload(database)
        self._db = database

    def teardown(self):
        remove_streamlit_mock()
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _path(self, label=""):
        return os.path.join(self._tmp, f"{label}_{uuid.uuid4().hex[:6]}.db")

    def _init(self, path):
        db = self._db; db.DB_NAME = path
        db.init_db(); db.init_energy_db(); db.init_water_db()

    def _user(self, path):
        db = self._db; db.DB_NAME = path
        u = f"u_{uuid.uuid4().hex[:6]}"
        db.create_user(u, f"{u}@t.com", "Pw1!")
        r = db.verify_user(u, "Pw1!")
        return r["id"] if r else 1

    def _cc(self, name):
        fn = getattr(self._db, name, None)
        if fn and hasattr(fn, "clear"): fn.clear()

    def _run_benchmarks(self):
        db = self._db; saved = db.DB_NAME

        # init_db
        def _init():
            p = self._path("i"); db.DB_NAME = p; db.init_db()
            db.DB_NAME = saved
            try: os.remove(p)
            except: pass
        self.measure("init_db – schema creation", _init)

        # create_user
        p1 = self._path("cu"); db.DB_NAME = p1; db.init_db()
        self.measure("create_user – bcrypt hash",
                     lambda: db.create_user(f"u{uuid.uuid4().hex[:6]}", "e@t.com", "Pw1!"))
        db.DB_NAME = saved

        # verify_user
        p2 = self._path("vu"); db.DB_NAME = p2; db.init_db()
        su = f"u_{uuid.uuid4().hex[:6]}"; db.create_user(su, f"{su}@t.com", "Pw2!")
        self.measure("verify_user – bcrypt check", lambda: db.verify_user(su, "Pw2!"))
        db.DB_NAME = saved

        # save / get assessments
        p3 = self._path("as"); self._init(p3); uid3 = self._user(p3); db.DB_NAME = p3
        self.measure("save_assessment – single insert",
                     lambda: db.save_assessment(uid3, "Car", 20, 250, "Non-Vegetarian", 2, 6293, 55))
        for _ in range(20): db.save_assessment(uid3, "Bus", 10, 180, "Vegetarian", 0, 3000, 70)
        self.measure("get_assessments – 20 rows", lambda: (self._cc("get_assessments"), db.get_assessments(uid3)))

        # bulk inserts
        p4 = self._path("bk"); self._init(p4); uid4 = self._user(p4); db.DB_NAME = p4
        self.measure("save_assessment – bulk 50 inserts",
                     lambda: [db.save_assessment(uid4,"Car",15,200,"Omnivore",1,4500,60) for _ in range(50)])
        self.measure("get_assessments – 50+ rows", lambda: (self._cc("get_assessments"), db.get_assessments(uid4)))
        db.DB_NAME = saved

        # appliances
        p5 = self._path("ap"); self._init(p5); uid5 = self._user(p5); db.DB_NAME = p5
        self.measure("add_appliance – single insert",
                     lambda: db.add_appliance(uid5, "Fridge", "Kitchen", 1, 150, 24, 5))
        for i in range(5): db.add_appliance(uid5, f"Dev{i}", "Room", 1, 50+i, 4, 1)
        self.measure("get_appliances – 6 rows", lambda: (self._cc("get_appliances"), db.get_appliances(uid5)))
        db.DB_NAME = saved

        # water
        p6 = self._path("wa"); self._init(p6); uid6 = self._user(p6); db.DB_NAME = p6
        self.measure("save_water_assessment – single insert",
                     lambda: db.save_water_assessment(uid6, 8, 3, 5, 30, "Vegan", 2950))
        for _ in range(10): db.save_water_assessment(uid6, 10, 4, 6, 20, "Vegetarian", 3100)
        self.measure("get_water_assessments – 11 rows",
                     lambda: (self._cc("get_water_assessments"), db.get_water_assessments(uid6)))
        db.DB_NAME = saved
