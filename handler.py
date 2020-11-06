from pdf2image import convert_from_bytes
from io import BytesIO
import traceback2 as traceback
import simplejson as json
import boto3


class pngResponse:
    status = ''
    statusMessage = ''
    pngS3Path = []

def exception_handler(e):
    pngResponseParameters = pngResponse()
    pngResponseParameters.status = "Error"
    pngResponseParameters.statusMessage = str(e)
    pngResponseParameters.pngS3Path = []
    return {                
        'body': json.dumps({"status":pngResponseParameters.status,"pngS3Path":pngResponseParameters.pngS3Path,"statusMessage":pngResponseParameters.statusMessage})
    }
    
def pdf2png(event,context):
    try:
        pngResponseParameters = pngResponse()
        s3 = boto3.resource("s3")
        s3Client = boto3.client("s3")
        lambdaClient = boto3.client("lambda")
        obj = s3.Object(event['s3Bucket'], '{0}/{1}/{2}.pdf'.format(event['inputFilePath'],event['shipmentId'],event['inputFileName']))
        infile = obj.get()['Body'].read()
        FMT = 'png'
        pngS3PathList = [] 
        images = convert_from_bytes(infile)
        for page_num, image in enumerate(images):  
            location = '{0}/{1}_{2}.{3}'.format(event['outputFilePath'],event['outputFileName'],str(page_num),FMT)
            buffer = BytesIO()
            image.save(buffer, FMT.upper())
            buffer.seek(0)
            s3.Object(event['s3Bucket'],location).put(Body=buffer)
            pngS3PathList.append("{0}/{1}/{2}_{3}.{4}".format(event['s3Url'],event['outputFilePath'],event['outputFileName'],str(page_num),FMT))
        
        pngResponseParameters.status = "Success"
        pngResponseParameters.pngS3Path = pngS3PathList
        pngResponseParameters.statusMessage = ""        
       
        s3Client.delete_object(Bucket=event['s3Bucket'],Key='{0}/{1}/{2}.pdf'.format(event['inputFilePath'],event['shipmentId'],event['inputFileName']))    

        inputParams = {
            "s3Path" : pngS3PathList,
            "shipmentId" : event['shipmentId']
        }
        response = lambdaClient.invoke(
            FunctionName = event['insertFunctionName'],
            InvocationType = 'Event',
            Payload = json.dumps(inputParams)
        )
        return {     
         'body': json.dumps({"status":pngResponseParameters.status,"pngS3Path":pngResponseParameters.pngS3Path,"statusMessage":pngResponseParameters.statusMessage})
        }
        
    except Exception as e:
        return exception_handler(traceback.format_exc())        

