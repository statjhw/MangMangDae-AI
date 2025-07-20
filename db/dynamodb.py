import os
from dotenv import load_dotenv
import boto3
from .logger import setup_logger

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
        self.table_name = "wanted_jobs"
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

if __name__ == "__main__":
    dynamodb = DynamoDB()
    count = 0
    for item in dynamodb.scan_items_generator("wanted_jobs"):
        if count >= 1 : 
            break
        count += 1
        print(item)