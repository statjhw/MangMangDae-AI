import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# 상위 디렉토리 경로를 추가하여 src 모듈을 import할 수 있도록 함
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from src.db import DynamoDB, Pinecone, Postgres

# DynamoDB 테스트
@patch('boto3.resource')
def test_dynamodb_init(mock_resource):
    # DynamoDB 초기화 테스트
    mock_table = MagicMock()
    mock_resource.return_value.Table.return_value = mock_table
    
    db = DynamoDB()
    assert db.table_name == "wanted_jobs"
    mock_resource.assert_called_once()

@patch('boto3.resource')
def test_dynamodb_get_item(mock_resource):
    # get_item 메서드 테스트
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': {'id': '123', 'title': '테스트 직무'}}
    mock_resource.return_value.Table.return_value = mock_table
    
    db = DynamoDB()
    item = db.get_item({'id': '123'})
    
    mock_table.get_item.assert_called_once_with(Key={'id': '123'})
    assert item == {'id': '123', 'title': '테스트 직무'}

@patch('boto3.resource')
def test_dynamodb_scan_items_generator(mock_resource):
    # scan_items_generator 메서드 테스트
    mock_table = MagicMock()
    # 첫 번째 페이지 결과와 두 번째 페이지 결과 설정
    mock_table.scan.side_effect = [
        {'Items': [{'id': '1'}, {'id': '2'}], 'LastEvaluatedKey': 'last_key'},
        {'Items': [{'id': '3'}, {'id': '4'}]}
    ]
    
    mock_resource.return_value.Table.return_value = mock_table
    
    db = DynamoDB()
    items = list(db.scan_items_generator('table_name', page_size=2))
    
    # 첫 번째 호출: 기본 scan
    # 두 번째 호출: LastEvaluatedKey를 사용한 scan
    assert mock_table.scan.call_count == 2
    assert len(items) == 4
    assert items == [{'id': '1'}, {'id': '2'}, {'id': '3'}, {'id': '4'}]

# Pinecone 테스트
@patch('src.db.PineconeVectorStore')
def test_pinecone_init(mock_pinecone):
    # Pinecone 초기화 테스트
    mock_pinecone.return_value = MagicMock()
    
    pc = Pinecone(embedding_model=MagicMock())
    
    assert pc.index_name == "mmdindex"
    mock_pinecone.assert_called_once()

# Postgres 테스트
@patch('psycopg2.connect')
def test_postgres_connect(mock_connect):
    # Postgres 연결 테스트
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    
    pg = Postgres()
    pg.connect()
    
    mock_connect.assert_called_once()
    assert pg.conn is not None
    assert pg.cursor is not None

@patch('psycopg2.connect')
def test_postgres_disconnect(mock_connect):
    # Postgres 연결 해제 테스트
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    
    pg = Postgres()
    pg.connect()
    pg.disconnect()
    
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once() 