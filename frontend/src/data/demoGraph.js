export const demoGraph = {
  text: `The Payment Service depends on Database A. Database A connects to Cache B for session storage. The Fraud Service calls the Payment Service. The Analytics Pipeline consumes events from Kafka. Kafka is managed by the Platform Team.`,
  nodes: [
    { id: 1, name: 'Payment Service', type: 'service' },
    { id: 2, name: 'Database A', type: 'database' },
    { id: 3, name: 'Cache B', type: 'cache' },
    { id: 4, name: 'Fraud Service', type: 'service' },
    { id: 5, name: 'Analytics Pipeline', type: 'pipeline' },
    { id: 6, name: 'Kafka', type: 'system' },
    { id: 7, name: 'Platform Team', type: 'team' },
  ],
  edges: [
    { id: 101, source_id: 1, target_id: 2, relation_type: 'depends_on' },
    { id: 102, source_id: 2, target_id: 3, relation_type: 'connects_to' },
    { id: 103, source_id: 4, target_id: 1, relation_type: 'calls' },
    { id: 104, source_id: 5, target_id: 6, relation_type: 'consumes' },
    { id: 105, source_id: 7, target_id: 6, relation_type: 'owns' },
  ],
};
