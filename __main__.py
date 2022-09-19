import pulumi
from pulumi_azure_native import storage
from pulumi_azure_native import resources
from pulumi_azure_native import network
from pulumi_azure_native import containerservice
from pulumi_azure_native import compute
import pulumi_azure_native as azure_native


prefix_name = "pulumiAKS"

vnet_ip_range = "192.168.0.0/16"
vm_ip_range = "192.168.16.0/24"

ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDfLeEbljcts7f6jxEnWvdfjAMoIL/yBY8DE4GgVJlWxg91sMAiq8BisxfJblu5GAq2MeHvgx3K8DS5RV49JpZApeAUEImiC3jqrvE7qF7YJg2fU5DITNavonUsvAxXz+64AS/o5MVv39zsjMbQrP9Chj5daO++n7gJfB7WJgNFhnNcl7Z4easj8CcsDlpfWx7CKwAacKtowNuDDJtcY9YuNloqVG0E6U3bSmnVGn/+uHkMvPd2sOLytwvj7aQ46AQoYWTUcqlu/67NQhi8kzPo4HKOI1J3j/ZczqIrxhfqxsj3+PVlst+oPnL74/dk6IjICpl8iIHNCVYe70lQX4DmTocpyPqYVgeCNqrG8ivhIeUOh2zfbKUyHZThYuDVsrCiJf93VAnfiy0jbpP6YEjWw2slvMsTwVPmc3ri4GtzQsix32JBQJ7AodUF+SUBQRCZASo4FbgtPN2JVVOHQZaBI9lza2E/s975N+ZWaAY7vIekqNChJkA963pdLjfI0LU= generated-by-azure"

# Create an Azure Resource Group
resource_group = resources.ResourceGroup(
    prefix_name+"-rg",
    resource_group_name=(prefix_name+"-rg"))

#Network security Groups
nsg = network.NetworkSecurityGroup(
    resource_name=(prefix_name+"-nsg"),
    network_security_group_name=(prefix_name+"-nsg"),
    resource_group_name=resource_group.name,
    security_rules=[network.SecurityRuleArgs(
        access="Allow",
        destination_address_prefix="*",
        destination_port_range="22",
        direction="Inbound",
        name="Allow-SSH",
        priority=130,
        protocol="*",
        source_address_prefix="*",
        source_port_range="*",
    )])

#Vnets and subnets
vnet = network.VirtualNetwork(
    prefix_name+"-vnet",
    address_space=network.AddressSpaceArgs(
        address_prefixes=[vnet_ip_range],
    ),
    resource_group_name=resource_group.name,
    virtual_network_name=(prefix_name+"-vnet"))

vm_subnet = network.Subnet(
    "vm-subnet",
    address_prefix=vm_ip_range,
    resource_group_name=resource_group.name,
    subnet_name="vm-subnet",
    virtual_network_name=vnet.name,
    network_security_group=network.NetworkSecurityGroupArgs(
        id=nsg.id
    ))

#virtual Machine
pip = network.PublicIPAddress(
    resource_name=(prefix_name+"-pip"),
    public_ip_address_name=(prefix_name+"-pip"),
    resource_group_name=resource_group.name
)

nic = network.NetworkInterface(
    resource_name=(prefix_name+"-nic"),
    ip_configurations=[network.NetworkInterfaceIPConfigurationArgs(
        name="ipconfig1",
        public_ip_address=network.PublicIPAddressArgs(
            id=pip.id,
        ),
        subnet=network.SubnetArgs(
            id=vm_subnet.id,
        ),
    )],
    network_interface_name=(prefix_name+"-nic"),
    resource_group_name=resource_group.name
)

vm = compute.VirtualMachine(
    resource_name=(prefix_name + "-vm"),
    hardware_profile=compute.HardwareProfileArgs(
        vm_size="Standard_B1s",
    ),
    network_profile=compute.NetworkProfileArgs(
    network_interfaces=[compute.NetworkInterfaceReferenceArgs(
            id=nic.id,
            primary=True,
        )],
    ),
    os_profile=compute.OSProfileArgs(
        admin_username="global",
        computer_name=(prefix_name + "-vm"),
        linux_configuration=compute.LinuxConfigurationArgs(
            disable_password_authentication=True,
            ssh=compute.SshConfigurationArgs(
                public_keys=[compute.SshPublicKeyArgs(
                    key_data = ssh_key,
                    path     = "/home/global/.ssh/authorized_keys",
                )],
            ),
        ),
    ),
    resource_group_name=resource_group.name,
    storage_profile=compute.StorageProfileArgs(
        image_reference=compute.ImageReferenceArgs(
            offer="UbuntuServer",
            publisher="Canonical",
            sku="18.04-LTS",
            version="latest",
        ),
        os_disk=compute.OSDiskArgs(
            caching="ReadWrite",
            create_option="FromImage",
            managed_disk=compute.ManagedDiskParametersArgs(
                storage_account_type="StandardSSD_LRS",
            ),
            name=(prefix_name + "-vm-osdisk"),
        ),
    ),
    vm_name=(prefix_name + "-vm")
)
# Create an Azure resource (Storage Account)
account = storage.StorageAccount('sa',
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(
        name=storage.SkuName.STANDARD_LRS,
    ),
    kind=storage.Kind.STORAGE_V2)

# Export the primary key of the Storage Account
primary_key = pulumi.Output.all(resource_group.name, account.name) \
    .apply(lambda args: storage.list_storage_account_keys(
        resource_group_name=args[0],
        account_name=args[1]
    )).apply(lambda accountKeys: accountKeys.keys[0].value)
    
#mysql server
server = azure_native.sql.Server("server",
    administrator_login="pulumi@srivastavajatin12gmail.onmicrosoft.com",
    administrator_login_password="Kola93418",
    administrators=azure_native.sql.ServerExternalAdministratorArgs(
        azure_ad_only_authentication=True,
        login="srivastava.jatin12@gmail.com",
        principal_type="User",
        sid=" 6d092d73-9ba1-43d6-b310-f019ac9350b3",
        tenant_id="22e5336b-2e4c-4414-8596-01e25584aaba",
    ),
    location="West US",
    resource_group_name="pulumiAKS-rgs",
    server_name="mysql-test")

#database
database = azure_native.sql.Database("database",
    database_name="mydb",
    location="West US",
    resource_group_name="pulumiAKS-rgs",
    server_name="mysql-test",
    sku=azure_native.sql.SkuArgs(
        name="S0",
        tier="Standard",
    ),
     source_database_id="/subscriptions/861c7352-89aa-43cf-83c7-5e655de5127d/resourceGroups/pulumiAKS-rgs/providers/Microsoft.Sql/servers/mysql-test/databases/testdb")


pulumi.export("primary_storage_key", primary_key)
                                                   
                                                                                                                                                                     


                                                                                                                                                                
























