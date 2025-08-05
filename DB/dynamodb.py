import os
from dotenv import load_dotenv
import boto3
from logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")


class DynamoDB:
    def __init__(self):
        self.access_key = AWS_ACCESS_KEY_ID
        self.secret_key = AWS_SECRET_ACCESS_KEY
        self.region = AWS_REGION
        self.dynamodb = boto3.resource(
            'dynamodb',  
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.table_name = "wanted_job"
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"DynamoDB class initialized. Table: {self.table_name}")
    
    def get_item(self, key):
        logger.debug(f"Attempting to get item with key: {key} from DynamoDB table: {self.table_name}")
        response = self.table.get_item(Key=key)
        item = response.get('Item')
        if item:
            logger.info(f"Successfully retrieved item with key: {key}")
        else:
            logger.warning(f"Item not found for key: {key}")
        return item

    def scan_items_generator(self, table_name, page_size=25):
        logger.info(f"Starting scan for DynamoDB table: {table_name} with page size: {page_size}")
        """
        DynamoDB 테이블의 항목을 페이지 단위로 반환하는 제너레이터입니다.
        메모리 사용량을 최적화하기 위해 한 번에 모든 항목을 로드하지 않고
        페이지 단위로 가져와 하나씩 반환합니다.
        
        Args:
            table_name (str): 테이블 이름
            page_size (int): 한 번에 가져올 항목 수 (기본값: 25)
            
        Yields:
            dict: 테이블의 각 항목
        """
        kwargs = {'Limit': page_size}
        
        # 첫 페이지 스캔
        response = self.table.scan(**kwargs)
        
        # 각 항목 반환
        for item in response['Items']:
            logger.debug(f"Yielding item: {item.get('url', 'N/A')} from scan") # Assuming 'url' exists for logging
            yield item
        
        # 페이지네이션 처리 - 다음 페이지가 있으면 계속 스캔
        while 'LastEvaluatedKey' in response:
            logger.debug(f"Fetching next page for scan, LastEvaluatedKey: {response['LastEvaluatedKey']}")
            kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.scan(**kwargs)
            
            for item in response['Items']:
                logger.debug(f"Yielding item: {item.get('url', 'N/A')} from paginated scan") # Assuming 'url' exists
                yield item
        logger.info(f"Finished scan for DynamoDB table: {table_name}") 
    
    def get_total_item_count(self):
        """
        DynamoDB 테이블의 총 문서(아이템) 개수를 반환합니다.
        실제 스캔을 통해 정확한 개수를 카운트합니다.
        
        Returns:
            int: 테이블의 총 아이템 개수
        """
        logger.info(f"Starting count of total items in table: {self.table_name}")
        count = 0
        
        try:
            # scan_items_generator를 사용하여 모든 아이템을 카운트
            for item in self.scan_items_generator(self.table_name):
                count += 1
            
            logger.info(f"Total item count in table {self.table_name}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error while counting items in table {self.table_name}: {str(e)}")
            raise e
    
    def get_table_description(self):
        """
        DynamoDB 테이블의 메타데이터를 반환합니다 (ItemCount 포함).
        주의: ItemCount는 실시간이 아니며 약 6시간마다 업데이트됩니다.
        
        Returns:
            dict: 테이블 설명 정보
        """
        try:
            response = self.table.meta.client.describe_table(TableName=self.table_name)
            table_info = response['Table']
            logger.info(f"Table description retrieved for {self.table_name}")
            return table_info
        except Exception as e:
            logger.error(f"Error while getting table description for {self.table_name}: {str(e)}")
            raise e

if __name__ == "__main__":
    dynamodb = DynamoDB()
    
    print("=== DynamoDB 테이블 정보 ===")
    
    # 방법 1: 테이블 메타데이터에서 ItemCount 확인 (실시간이 아님)
    try:
        table_info = dynamodb.get_table_description()
        estimated_count = table_info.get('ItemCount', 0)
        print(f"테이블명: {table_info['TableName']}")
        print(f"예상 문서 개수 (메타데이터): {estimated_count:,}개")
        print(f"테이블 상태: {table_info['TableStatus']}")
        print(f"생성일: {table_info['CreationDateTime']}")
    except Exception as e:
        print(f"테이블 메타데이터 조회 실패: {e}")
    
    print("\n" + "="*50)
    
    # 방법 2: 실제 스캔을 통한 정확한 문서 개수 확인
    try:
        print("실제 문서 개수를 확인 중... (시간이 소요될 수 있습니다)")
        actual_count = dynamodb.get_total_item_count()
        print(f"실제 문서 개수 (스캔 결과): {actual_count:,}개")
    except Exception as e:
        print(f"실제 문서 개수 확인 실패: {e}")
    
    print("\n" + "="*50 + "\n")