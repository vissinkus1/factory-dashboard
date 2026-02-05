import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'factory_dashboard.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # SQL Schema
    schema = """
    CREATE TABLE IF NOT EXISTS workers (
        worker_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS workstations (
        station_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP NOT NULL,
        worker_id TEXT NOT NULL,
        station_id TEXT NOT NULL,
        event_type TEXT NOT NULL CHECK(event_type IN ('working', 'idle', 'absent', 'product_count')),
        confidence REAL,
        count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (worker_id) REFERENCES workers(worker_id),
        FOREIGN KEY (station_id) REFERENCES workstations(station_id)
    );

    CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
    CREATE INDEX IF NOT EXISTS idx_events_worker ON events(worker_id);
    CREATE INDEX IF NOT EXISTS idx_events_station ON events(station_id);
    """
    
    cursor.executescript(schema)
    conn.commit()
    conn.close()

def seed_database():
    """Populate database with dummy data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM events')
    cursor.execute('DELETE FROM workstations')
    cursor.execute('DELETE FROM workers')
    
    # Insert workers
    workers = [
        ('W1', 'Alice Johnson'),
        ('W2', 'Bob Smith'),
        ('W3', 'Carol Davis'),
        ('W4', 'David Wilson'),
        ('W5', 'Emma Brown'),
        ('W6', 'Frank Miller'),
    ]
    cursor.executemany('INSERT INTO workers (worker_id, name) VALUES (?, ?)', workers)
    
    # Insert workstations
    stations = [
        ('S1', 'Assembly Line 1', 'assembly'),
        ('S2', 'Assembly Line 2', 'assembly'),
        ('S3', 'Quality Check', 'inspection'),
        ('S4', 'Packaging', 'packaging'),
        ('S5', 'Welding Station', 'welding'),
        ('S6', 'Testing Station', 'testing'),
    ]
    cursor.executemany('INSERT INTO workstations (station_id, name, type) VALUES (?, ?, ?)', stations)
    
    # Generate sample events for the past day
    base_time = datetime.utcnow() - timedelta(days=1)
    events = []
    
    for day_offset in range(2):  # 2 days of data
        for hour in range(8, 17):  # 8 AM to 5 PM
            for worker_id in ['W1', 'W2', 'W3', 'W4', 'W5', 'W6']:
                event_time = base_time + timedelta(days=day_offset, hours=hour)
                
                # Working event
                events.append((
                    event_time.isoformat() + 'Z',
                    worker_id,
                    f'S{((ord(worker_id[1])-ord("1")) % 6) + 1}',  # Assign to stations
                    'working',
                    0.95,
                    0
                ))
                
                # Random idle events
                if hour % 3 == 0:
                    idle_time = event_time + timedelta(minutes=15)
                    events.append((
                        idle_time.isoformat() + 'Z',
                        worker_id,
                        f'S{((ord(worker_id[1])-ord("1")) % 6) + 1}',
                        'idle',
                        0.88,
                        0
                    ))
                
                # Product count events
                if hour % 2 == 0:
                    product_time = event_time + timedelta(minutes=30)
                    events.append((
                        product_time.isoformat() + 'Z',
                        worker_id,
                        f'S{((ord(worker_id[1])-ord("1")) % 6) + 1}',
                        'product_count',
                        0.92,
                        5 + (hash(worker_id + str(hour)) % 6)  # 5-10 units
                    ))
    
    cursor.executemany(
        'INSERT INTO events (timestamp, worker_id, station_id, event_type, confidence, count) VALUES (?, ?, ?, ?, ?, ?)',
        events
    )
    
    conn.commit()
    conn.close()

def get_workers() -> List[Dict]:
    """Get all workers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT worker_id, name FROM workers ORDER BY worker_id')
    workers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return workers

def get_workstations() -> List[Dict]:
    """Get all workstations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT station_id, name, type FROM workstations ORDER BY station_id')
    stations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stations

def insert_event(event_data: Dict) -> bool:
    """Insert a single event"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO events (timestamp, worker_id, station_id, event_type, confidence, count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            event_data['timestamp'],
            event_data['worker_id'],
            event_data['workstation_id'],
            event_data['event_type'],
            event_data.get('confidence', 0.0),
            event_data.get('count', 0)
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error inserting event: {e}")
        return False

def get_worker_metrics(worker_id: str) -> Dict:
    """Calculate metrics for a specific worker"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get worker info
    cursor.execute('SELECT name FROM workers WHERE worker_id = ?', (worker_id,))
    worker = cursor.fetchone()
    if not worker:
        conn.close()
        return None
    
    # Get all events for worker
    cursor.execute('''
        SELECT timestamp, event_type, count FROM events 
        WHERE worker_id = ? 
        ORDER BY timestamp
    ''', (worker_id,))
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Calculate metrics
    working_time = 0
    idle_time = 0
    total_products = 0
    
    # Parse timestamps and calculate durations
    prev_event = None
    for event in events:
        timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        
        if prev_event:
            prev_timestamp = datetime.fromisoformat(prev_event['timestamp'].replace('Z', '+00:00'))
            duration_seconds = (timestamp - prev_timestamp).total_seconds()
            
            if prev_event['event_type'] == 'working':
                working_time += duration_seconds
            elif prev_event['event_type'] == 'idle':
                idle_time += duration_seconds
        
        if event['event_type'] == 'product_count':
            total_products += event['count']
        
        prev_event = event
    
    # Convert to hours
    working_hours = working_time / 3600
    idle_hours = idle_time / 3600
    total_hours = working_hours + idle_hours
    
    utilization_pct = (working_hours / total_hours * 100) if total_hours > 0 else 0
    units_per_hour = (total_products / working_hours) if working_hours > 0 else 0
    
    return {
        'worker_id': worker_id,
        'name': worker['name'],
        'total_active_time_hours': round(working_hours, 2),
        'total_idle_time_hours': round(idle_hours, 2),
        'utilization_percentage': round(utilization_pct, 2),
        'total_units_produced': total_products,
        'units_per_hour': round(units_per_hour, 2),
        'event_count': len(events)
    }

def get_workstation_metrics(station_id: str) -> Dict:
    """Calculate metrics for a specific workstation"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get station info
    cursor.execute('SELECT name, type FROM workstations WHERE station_id = ?', (station_id,))
    station = cursor.fetchone()
    if not station:
        conn.close()
        return None
    
    # Get all events for station
    cursor.execute('''
        SELECT timestamp, event_type, count FROM events 
        WHERE station_id = ? 
        ORDER BY timestamp
    ''', (station_id,))
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Calculate metrics
    occupied_time = 0
    total_products = 0
    
    prev_event = None
    for event in events:
        timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        
        if prev_event:
            prev_timestamp = datetime.fromisoformat(prev_event['timestamp'].replace('Z', '+00:00'))
            duration_seconds = (timestamp - prev_timestamp).total_seconds()
            
            if prev_event['event_type'] in ['working', 'idle']:
                occupied_time += duration_seconds
        
        if event['event_type'] == 'product_count':
            total_products += event['count']
        
        prev_event = event
    
    occupied_hours = occupied_time / 3600
    throughput_rate = (total_products / occupied_hours) if occupied_hours > 0 else 0
    
    return {
        'station_id': station_id,
        'name': station['name'],
        'type': station['type'],
        'occupancy_time_hours': round(occupied_hours, 2),
        'utilization_percentage': 85.0,  # Placeholder, could be more sophisticated
        'total_units_produced': total_products,
        'throughput_rate': round(throughput_rate, 2),
        'event_count': len(events)
    }

def get_factory_metrics() -> Dict:
    """Calculate factory-level metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all events
    cursor.execute('''
        SELECT timestamp, event_type, count FROM events 
        ORDER BY timestamp
    ''')
    events = [dict(row) for row in cursor.fetchall()]
    
    # Get worker count
    cursor.execute('SELECT COUNT(*) as count FROM workers')
    worker_count = cursor.fetchone()['count']
    
    # Get station count
    cursor.execute('SELECT COUNT(*) as count FROM workstations')
    station_count = cursor.fetchone()['count']
    conn.close()
    
    # Calculate factory metrics
    total_productive_time = 0
    total_production = 0
    total_working_time = 0
    
    prev_event = None
    for event in events:
        timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        
        if prev_event:
            prev_timestamp = datetime.fromisoformat(prev_event['timestamp'].replace('Z', '+00:00'))
            duration_seconds = (timestamp - prev_timestamp).total_seconds()
            
            if prev_event['event_type'] == 'working':
                total_productive_time += duration_seconds
                total_working_time += duration_seconds
            elif prev_event['event_type'] == 'idle':
                total_working_time += duration_seconds
        
        if event['event_type'] == 'product_count':
            total_production += event['count']
        
        prev_event = event
    
    productive_hours = total_productive_time / 3600
    working_hours = total_working_time / 3600
    avg_utilization = (productive_hours / working_hours * 100) if working_hours > 0 else 0
    production_rate = (total_production / productive_hours) if productive_hours > 0 else 0
    
    return {
        'total_productive_time_hours': round(productive_hours, 2),
        'total_production_count': total_production,
        'average_production_rate': round(production_rate, 2),
        'average_utilization_percentage': round(avg_utilization, 2),
        'worker_count': worker_count,
        'station_count': station_count,
        'total_events': len(events)
    }

def get_all_worker_metrics() -> List[Dict]:
    """Get metrics for all workers"""
    workers = get_workers()
    return [get_worker_metrics(w['worker_id']) for w in workers]

def get_all_workstation_metrics() -> List[Dict]:
    """Get metrics for all workstations"""
    stations = get_workstations()
    return [get_workstation_metrics(s['station_id']) for s in stations]
