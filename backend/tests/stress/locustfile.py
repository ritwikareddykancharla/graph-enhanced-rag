"""
Locust stress testing for Graph-Enhanced RAG API

Usage:
    locust -f locustfile.py --host http://localhost:8000

For headless mode:
    locust -f locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 60s --html report.html
"""

import random
import string
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


def random_string(length=10):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_architecture_text():
    templates = [
        "The {service} Service depends on the {db} Database for data storage. "
        "The {service} Service connects to the {cache} Cache for session management. "
        "The {api} API calls the {service} Service for business logic. "
        "The {db} Database replicates to the {analytics} Analytics platform. "
        "The {frontend} Frontend communicates with the {api} API gateway.",
        "Microservice {name} uses {dep} for dependency injection. "
        "Component {a} connects to component {b} via REST API. "
        "The {queue} Message Queue feeds into the {worker} Worker process.",
        "Service {svc1} depends on Service {svc2} which connects to Database {db}. "
        "The {gateway} API Gateway routes to {svc1}, {svc2}, and {svc3}. "
        "Cache layer {cache} sits in front of {db} reducing query load by 80%.",
    ]

    services = [
        "Payment",
        "Auth",
        "User",
        "Order",
        "Inventory",
        "Notification",
        "Email",
        "Search",
    ]
    dbs = ["Postgres", "MySQL", "MongoDB", "Redis", "Elasticsearch"]
    components = ["API", "Worker", "Gateway", "Frontend", "Mobile", "Admin"]

    template = random.choice(templates)

    return template.format(
        service=random.choice(services),
        db=random.choice(dbs),
        cache=random.choice(dbs),
        api=random.choice(components),
        analytics="Analytics",
        frontend="Web",
        name=random_string(8),
        dep=random_string(6),
        a=random_string(5),
        b=random_string(5),
        queue="Kafka",
        worker="Celery",
        svc1=random.choice(services),
        svc2=random.choice(services),
        svc3=random.choice(services),
        gateway="Kong",
        cache_layer=random.choice(dbs),
    )


class GraphRAGUser(HttpUser):
    """
    Simulated user for Graph-Enhanced RAG API stress testing.
    """

    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.api_key = "test-stress-key"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        self.created_node_ids = []
        self.created_edge_ids = []

        self.health_check()

    def health_check(self):
        """Verify API is responsive before starting tests."""
        self.client.get("/health", name="health_check", headers=self.headers)

    @task(10)
    def ingest_text(self):
        """Test text ingestion endpoint - most common operation."""
        text = generate_architecture_text()
        payload = {
            "text": text,
            "metadata": {"source": "stress_test", "batch_id": random_string(8)},
        }

        with self.client.post(
            "/ingest/text",
            json=payload,
            headers=self.headers,
            name="ingest_text",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "nodes" in data:
                    self.created_node_ids.extend(
                        [n["id"] for n in data.get("nodes", [])]
                    )
                response.success()
            elif response.status_code == 429:
                response.success()  # Rate limit hit - expected behavior
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def list_nodes(self):
        """Test node listing with pagination."""
        params = {"skip": random.randint(0, 50), "limit": random.randint(10, 50)}

        self.client.get(
            "/graph/nodes", params=params, headers=self.headers, name="list_nodes"
        )

    @task(5)
    def list_edges(self):
        """Test edge listing with pagination."""
        params = {"skip": random.randint(0, 50), "limit": random.randint(10, 50)}

        self.client.get(
            "/graph/edges", params=params, headers=self.headers, name="list_edges"
        )

    @task(3)
    def search_nodes(self):
        """Test node search functionality."""
        search_terms = [
            "Service",
            "Database",
            "API",
            "Payment",
            "Auth",
            "User",
            "Cache",
        ]
        params = {"name": random.choice(search_terms), "limit": 20}

        self.client.get(
            "/graph/nodes", params=params, headers=self.headers, name="search_nodes"
        )

    @task(2)
    def impact_analysis(self):
        """Test impact analysis - computationally expensive operation."""
        if not self.created_node_ids:
            self.client.get(
                "/graph/nodes",
                params={"limit": 10},
                headers=self.headers,
                name="get_nodes_for_impact",
            )
            return

        node_id = (
            random.choice(self.created_node_ids[-20:])
            if len(self.created_node_ids) > 20
            else self.created_node_ids[0]
        )

        payload = {"node_id": node_id, "max_depth": random.randint(3, 7)}

        self.client.post(
            "/graph/query/impact",
            json=payload,
            headers=self.headers,
            name="impact_analysis",
        )

    @task(1)
    def path_finding(self):
        """Test path finding - most complex graph operation."""
        if len(self.created_node_ids) < 2:
            return

        source_id = random.choice(self.created_node_ids)
        target_id = random.choice([n for n in self.created_node_ids if n != source_id])

        payload = {
            "source_id": source_id,
            "target_id": target_id,
            "max_depth": random.randint(5, 10),
        }

        with self.client.post(
            "/graph/query/path",
            json=payload,
            headers=self.headers,
            name="path_finding",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Path not found is valid
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class HeavyIngestionUser(HttpUser):
    """
    User that focuses on heavy ingestion operations.
    Used to test ingestion pipeline under load.
    """

    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.api_key = "test-stress-key"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    @task
    def bulk_ingest(self):
        """Send large text payloads for ingestion."""
        texts = [generate_architecture_text() for _ in range(5)]
        combined_text = " ".join(texts)

        payload = {
            "text": combined_text,
            "metadata": {"source": "bulk_stress_test", "batch_id": random_string(8)},
        }

        with self.client.post(
            "/ingest/text",
            json=payload,
            headers=self.headers,
            name="bulk_ingest",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 429]:
                response.success()
            else:
                response.failure(f"Bulk ingest failed: {response.status_code}")


class QueryOnlyUser(HttpUser):
    """
    User that only queries the graph - simulates read-heavy workload.
    """

    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.api_key = "test-stress-key"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        self.node_ids = []
        self._fetch_node_ids()

    def _fetch_node_ids(self):
        response = self.client.get(
            "/graph/nodes",
            params={"limit": 100},
            headers=self.headers,
            name="prefetch_nodes",
        )
        if response.status_code == 200:
            data = response.json()
            self.node_ids = [n["id"] for n in data.get("nodes", [])]

    @task(5)
    def get_node(self):
        if not self.node_ids:
            return

        node_id = random.choice(self.node_ids)
        self.client.get(
            f"/graph/nodes/{node_id}", headers=self.headers, name="get_single_node"
        )

    @task(3)
    def get_edges_for_node(self):
        if not self.node_ids:
            return

        node_id = random.choice(self.node_ids)
        self.client.get(
            "/graph/edges",
            params={"source_id": node_id},
            headers=self.headers,
            name="get_node_edges",
        )

    @task(2)
    def explore_graph(self):
        """Simulate user exploring the graph by clicking nodes."""
        if len(self.node_ids) < 2:
            return

        start_node = random.choice(self.node_ids)

        with self.client.post(
            "/graph/query/impact",
            json={"node_id": start_node, "max_depth": 3},
            headers=self.headers,
            name="explore_impact",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "=" * 60)
    print("Graph-Enhanced RAG Stress Test")
    print("=" * 60)
    print(f"Target: {environment.host}")
    print(f"User classes: {[u.__name__ for u in environment.user_classes]}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "=" * 60)
    print("Stress Test Complete")
    print("=" * 60)

    if hasattr(environment, "stats"):
        stats = environment.stats
        print(f"Total requests: {stats.total.num_requests}")
        print(f"Total failures: {stats.total.num_failures}")
        print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
        print(f"Requests/sec: {stats.total.total_rps:.2f}")
        print(f"50th percentile: {stats.total.get_response_time_percentile(0.5):.2f}ms")
        print(
            f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms"
        )
        print(
            f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms"
        )

    print("=" * 60 + "\n")
