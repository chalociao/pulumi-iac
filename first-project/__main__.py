"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws
from pulumi_aws import s3

# Create an AWS resource (S3 Bucket)
bucket = s3.BucketV2('my-bucket')

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)

####EC2
vpc = pulumi_aws.ec2.Vpc("vpc", cidr_block="10.0.0.0/16")
igw = pulumi_aws.ec2.InternetGateway("gateway", vpc_id=vpc.id)

subnet = pulumi_aws.ec2.Subnet("subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True
)

routes = pulumi_aws.ec2.RouteTable("routes",
    vpc_id=vpc.id,
    routes=[
        pulumi_aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id
        ),
        
    ],
)

route_table_association = pulumi_aws.ec2.RouteTableAssociation("route_table_association",
    subnet_id=subnet.id,
    route_table_id=routes.id
)

security_group = pulumi_aws.ec2.SecurityGroup("security-group",
    vpc_id=vpc.id,
    ingress=[
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            cidr_blocks=["0.0.0.0/0"],
            protocol="tcp",
            from_port=80,
            to_port=80
        )
    ],
    egress=[
        pulumi_aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=0,
            protocol="-1"
        )
    ]
)

ami = pulumi.Output.from_input(pulumi_aws.ec2.get_ami(
    owners=["amazon"],
    most_recent=True,
    filters=[{"name": "description", "values": ["Amazon Linux 2 *"]}],
)).apply(lambda ami: ami.id)

instance = pulumi_aws.ec2.Instance("new-test-vm",
    ami=ami,
    instance_type="t3.micro",
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    user_data="""
        #!/bin/bash
        yum update -y
        yum install -y httpd
        systemctl start httpd
        systemctl enable httpd
        echo "<h1>Hello World from $(hostname -f)</h1>" > /var/www/html/index.html
    """
)

pulumi.export("instanceURL", pulumi.Output.concat("http://", instance.public_ip))
